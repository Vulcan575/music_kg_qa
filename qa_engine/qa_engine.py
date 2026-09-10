# -*- coding: utf-8 -*-
"""
智能问答引擎模块
包含自然语言理解、Cypher查询生成、答案生成三个子模块
"""

import re
import json
import requests
from neo4j import GraphDatabase
import config

class QAEngine:
    """问答引擎"""

    # Cypher查询模板
    # 键的构造顺序为 (实体类型, 关系类型, 问题类型)，须与 generate_cypher() 中的 key 保持一致
    TEMPLATES = {
        ("Singer", "SING", "song"): """
            MATCH (s:Singer {singer_name: $entity})-[r:SING]->(song:Song)
            RETURN song.song_name AS name
            LIMIT 20
        """,
        # "songs" 与 "song" 同义：正则模板用单数，DeepSeek 意图识别习惯返回复数，
        # 两个词表须在此对齐，否则第二轨识别出的意图无法映射到模板
        ("Singer", "SING", "songs"): """
            MATCH (s:Singer {singer_name: $entity})-[r:SING]->(song:Song)
            RETURN song.song_name AS name
            LIMIT 20
        """,
        ("Song", "BELONG_TO", "singer"): """
            MATCH (song:Song {song_name: $entity})<-[:SING]-(singer:Singer)
            RETURN singer.singer_name AS name
            LIMIT 20
        """,
        ("Song", "IN_ALBUM", "album"): """
            MATCH (song:Song {song_name: $entity})-[:IN_ALBUM]->(album:Album)
            RETURN album.name AS name
            LIMIT 10
        """,
        ("Album", "IN_ALBUM", "songs"): """
            MATCH (album:Album {name: $entity})<-[:IN_ALBUM]-(song:Song)
            RETURN song.song_name AS name
            LIMIT 20
        """,
        ("Singer", "SING", "album"): """
            MATCH (s:Singer {singer_name: $entity})-[:SING]->(song:Song)-[:IN_ALBUM]->(album:Album)
            RETURN DISTINCT album.name AS name
            LIMIT 20
        """,
        ("Singer", "SING", "count"): """
            MATCH (s:Singer {singer_name: $entity})-[r:SING]->(song:Song)
            RETURN count(song) AS count
        """,
        ("Singer", "COLLABORATE", "collaborate"): """
            MATCH (s1:Singer {singer_name: $entity})-[r:COLLABORATE]-(s2:Singer)
            RETURN DISTINCT s2.singer_name AS name
            LIMIT 20
        """
    }

    def __init__(self):
        """初始化问答引擎"""
        self.driver = None
        self.neo4j_config = config.NEO4J_CONFIG
        self.deepseek_config = config.DEEPSEEK_CONFIG
        self._connect_neo4j()

    def _connect_neo4j(self):
        """连接Neo4j数据库"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_config["URI"],
                auth=(self.neo4j_config["USER"], self.neo4j_config["PASSWORD"])
            )
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("Neo4j 连接成功")
        except Exception as e:
            print(f"Neo4j 连接失败: {e}")
            print("请检查 config.py 中 NEO4J_CONFIG 的 URI/USER/PASSWORD 是否正确。")
            self.driver = None

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()

    def get_entity_property(self, entity_type):
        """获取实体名属性名称，用于兼容不同标签的属性字段"""
        return {
            "Singer": "singer_name",
            "Song": "song_name",
            "Music": "song_name",
            "Album": "name",
            "Tag": "name"
        }.get(entity_type, "name")

    def _extract_json_from_text(self, text):
        """从模型返回文本中提取第一个JSON对象"""
        try:
            return json.loads(text)
        except Exception:
            match = re.search(r"(\{[\s\S]*\})", text)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    return None
        return None

    def ask_deepseek(self, question, system_prompt=None):
        """调用DeepSeek大模型进行开放式问答"""
        api_key = self.deepseek_config.get("API_KEY", "")
        base_url = self.deepseek_config.get("BASE_URL", "").rstrip("/")
        if not api_key or not base_url:
            return None

        if system_prompt is None:
            system_prompt = "你是一个音乐知识图谱问答助手。请用简洁中文回答用户问题，优先使用已有的知识图谱数据。"

        url = f"{base_url}/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.deepseek_config.get("MODEL", "deepseek-chat"),
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "temperature": self.deepseek_config.get("TEMPERATURE", 0.3),
            "max_tokens": self.deepseek_config.get("MAX_TOKENS", 1024)
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=self.deepseek_config.get("TIMEOUT", 30))
            response.raise_for_status()
            data = response.json()
            if isinstance(data, dict):
                choices = data.get("choices") or data.get("data")
                if isinstance(choices, list) and choices:
                    choice = choices[0]
                    if isinstance(choice, dict):
                        if choice.get("message"):
                            return choice["message"].get("content")
                        if choice.get("text"):
                            return choice.get("text")
                if "result" in data and isinstance(data["result"], str):
                    return data["result"]
                if "output" in data and isinstance(data["output"], str):
                    return data["output"]
            if isinstance(data, str):
                return data
            return None
        except Exception as e:
            print(f"DeepSeek接口调用失败: {e}")
            return None

    def ask_deepseek_json(self, question, system_prompt):
        """从DeepSeek获取JSON格式的结构化返回"""
        answer = self.ask_deepseek(question, system_prompt=system_prompt)
        if not answer:
            return None
        return self._extract_json_from_text(answer)

    def ask_deepseek_intent(self, question):
        """使用DeepSeek辅助获取意图、实体、关系和问题类型"""
        prompt = (
            "你是音乐知识图谱问答系统的NLU模块。请分析用户的问题，返回一个JSON对象，"
            "包含entity_type, entity_name, relation_type, question_type。"
            "entity_type只能是 Singer、Song、Album、Tag、unknown；"
            "relation_type只能是 SING、BELONG_TO、IN_ALBUM、COLLABORATE、count、unknown；"
            "question_type只能是 song、singer、album、songs、collaborate、count、complex、unknown。"
            "不要输出解释，只输出合法JSON，例如 {\"entity_type\": \"Singer\", \"entity_name\": \"周杰伦\", \"relation_type\": \"SING\", \"question_type\": \"song\"}."
        )
        result = self.ask_deepseek_json(question, prompt)
        if not isinstance(result, dict):
            return None
        if all(k in result for k in ("entity_type", "entity_name", "relation_type", "question_type")):
            return {
                "entity_type": result["entity_type"],
                "entity_name": result["entity_name"],
                "relation_type": result["relation_type"],
                "question_type": result["question_type"]
            }
        return None

    def parse_intent(self, question):
        """
        解析用户问句意图
        返回: dict 包含 entity_type, entity_name, relation_type, question_type
        """
        question = question.strip()

        patterns = [
            (r"(.+)演唱了哪些歌曲", "Singer", "song", "SING"),
            (r"(.+)演唱过哪些歌曲", "Singer", "song", "SING"),
            (r"有哪些歌曲是(.+)演唱的", "Singer", "song", "SING"),
            (r"谁演唱了《(.+)》", "Song", "singer", "BELONG_TO"),
            (r"谁唱过《(.+)》", "Song", "singer", "BELONG_TO"),
            (r"《(.+)》是谁唱的", "Song", "singer", "BELONG_TO"),
            (r"《(.+)》的歌手是谁", "Song", "singer", "BELONG_TO"),
            (r"(.+)有多少首歌", "Singer", "count", "SING"),
            (r"(.+)合作过哪些歌手", "Singer", "collaborate", "COLLABORATE"),
            (r"(.+)和谁合作", "Singer", "collaborate", "COLLABORATE"),
            (r"《(.+)》在哪个专辑", "Song", "album", "IN_ALBUM"),
            (r"《(.+)》收录在哪张专辑", "Song", "album", "IN_ALBUM"),
            (r"哪些歌曲收录在(.+)专辑", "Album", "songs", "IN_ALBUM"),
            (r"(.+)有哪些专辑", "Singer", "album", "SING"),
            (r"(.+)的专辑有哪些", "Singer", "album", "SING"),
        ]

        for pattern, entity_type, question_type, relation_type in patterns:
            match = re.match(pattern, question)
            if match:
                entity_name = match.group(1).strip()
                entity_name = entity_name.strip('"').strip("'")
                return {
                    "entity_type": entity_type,
                    "entity_name": entity_name,
                    "relation_type": relation_type,
                    "question_type": question_type
                }

        return {
            "entity_type": "unknown",
            "entity_name": question,
            "relation_type": "unknown",
            "question_type": "complex"
        }

    def generate_cypher(self, intent):
        """
        生成Cypher查询语句
        采用模板匹配优先策略
        """
        key = (intent["entity_type"], intent["relation_type"], intent.get("question_type", ""))

        if key in self.TEMPLATES:
            return self.TEMPLATES[key]

        entity_prop = self.get_entity_property(intent["entity_type"])
        if intent["question_type"] == "count":
            return f"""
                MATCH (s:{intent['entity_type']} {{{entity_prop}: $entity}})-[r]->(m)
                RETURN count(m) AS count
            """

        return f"""
            MATCH (n:{intent['entity_type']} {{{entity_prop}: $entity}})
            RETURN coalesce(n.name, n.singer_name, n.song_name, n.album_name) AS name
            LIMIT 10
        """

    def execute_query(self, cypher, params):
        """执行Cypher查询"""
        if not self.driver:
            print("查询失败：Neo4j 未连接")
            return []
        try:
            with self.driver.session() as session:
                result = session.run(cypher, **params)
                return [dict(record) for record in result]
        except Exception as e:
            print(f"查询执行失败: {e}")
            return []

    def search_entity_by_name(self, text):
        """通过名称模糊搜索知识图谱实体"""
        query = """
            MATCH (n)
            WHERE coalesce(n.name, n.singer_name, n.song_name, n.album_name) CONTAINS $text
            RETURN labels(n)[0] AS type, coalesce(n.name, n.singer_name, n.song_name, n.album_name) AS name
            LIMIT 20
        """
        return self.execute_query(query, {"text": text})

    def format_answer(self, question, intent, results):
        """格式化答案文本"""
        entity_name = intent["entity_name"]
        question_type = intent["question_type"]

        if not results:
            return f"抱歉，我在知识图谱中没有找到与'{entity_name}'相关的答案。"

        if question_type == "count":
            count = results[0].get("count", 0)
            return f"根据知识图谱数据，'{entity_name}'相关结果共有 {count} 条。"

        if question_type in ["song", "singer", "collaborate", "album", "songs"]:
            names = [r.get("name", "") for r in results if r.get("name")]
            if not names:
                return f"抱歉，没有找到与'{entity_name}'相关的详细信息。"
            return f"与'{entity_name}'相关的结果：\n" + "\n".join(f"  {i+1}. {name}" for i, name in enumerate(names))

        return f"找到 {len(results)} 条相关结果"

    def _build_graph_data(self, intent, results):
        """构建图谱可视化数据"""
        nodes = [
            {
                "id": 0,
                "label": intent["entity_name"],
                "type": intent["entity_type"],
                "size": 30,
                "color": "#ff6b6b"
            }
        ]
        edges = []

        for idx, result in enumerate(results[:10], start=1):
            name = result.get("name", "")
            if name and name != intent["entity_name"]:
                nodes.append({
                    "id": idx,
                    "label": name,
                    "type": intent.get("relation_type", "result"),
                    "size": 20,
                    "color": "#4ecdc4"
                })
                edges.append({
                    "from": 0,
                    "to": idx,
                    "relation": intent.get("relation_type", "关联")
                })

        return {"nodes": nodes, "edges": edges}

    def handle_complex_question(self, question, intent):
        """复杂问题处理：尝试实体模糊匹配，然后调用大模型"""
        candidates = self.search_entity_by_name(question)
        if candidates:
            answer = "我在知识图谱中找到以下可能相关的实体：\n" + "\n".join(
                f"  {idx+1}. [{item.get('type')}] {item.get('name')}" for idx, item in enumerate(candidates)
            )
            graph_data = {
                "nodes": [
                    {"id": 0, "label": question, "type": "Query", "size": 30, "color": "#ff6b6b"}
                ] + [
                    {"id": idx + 1, "label": item.get("name"), "type": item.get("type"), "size": 20, "color": "#4ecdc4"}
                    for idx, item in enumerate(candidates[:10])
                ],
                "edges": [
                    {"from": 0, "to": idx + 1, "relation": "可能相关"}
                    for idx in range(len(candidates[:10]))
                ]
            }
            return {
                "answer": answer,
                "cypher": "",
                "intent": intent,
                "results": candidates,
                "graph_data": graph_data
            }

        deepseek_answer = self.ask_deepseek(question)
        if deepseek_answer:
            return {
                "answer": deepseek_answer,
                "cypher": "",
                "intent": intent,
                "results": [],
                "graph_data": {"nodes": [], "edges": []}
            }

        return None

    def answer(self, question):
        """回答用户问题"""
        intent = self.parse_intent(question)
        print(f"[意图解析] {intent}")

        # 第二轨：正则模板未命中（question_type 为 complex）时，交给 DeepSeek 做意图识别。
        # 仅当识别结果能映射到某个 Cypher 模板时才采纳 —— 否则说明大模型只识别出了实体、
        # 没识别出关系（如"XX是谁"），此时保留 complex，继续走模糊匹配 / 开放问答兜底。
        if intent["question_type"] == "complex":
            deepseek_intent = self.ask_deepseek_intent(question)
            if deepseek_intent:
                ds_key = (
                    deepseek_intent["entity_type"],
                    deepseek_intent["relation_type"],
                    deepseek_intent["question_type"],
                )
                if ds_key in self.TEMPLATES:
                    intent = deepseek_intent
                    print(f"[DeepSeek 意图] {intent}")

        cypher = self.generate_cypher(intent)
        print(f"[Cypher查询] {cypher[:120]}...")

        results = self.execute_query(cypher, {"entity": intent["entity_name"], "text": intent["entity_name"]})
        print(f"[查询结果] 找到 {len(results)} 条记录")

        if not results and intent["question_type"] in ("complex", "unknown"):
            complex_result = self.handle_complex_question(question, intent)
            if complex_result:
                return complex_result

        answer = self.format_answer(question, intent, results)
        graph_data = self._build_graph_data(intent, results)

        return {
            "answer": answer,
            "cypher": cypher.strip(),
            "intent": intent,
            "results": results,
            "graph_data": graph_data
        }

    def extract_knowledge_to_neo4j(self, question, answer):
        """
        从DeepSeek的回答中提取音乐知识，以JSON格式写入Neo4j。
        仅提取有价值的音乐知识（歌手、歌曲、专辑、标签及其关系），
        不写入无关内容。
        """
        if not self.driver:
            print("[知识回写] Neo4j 未连接，跳过知识回写")
            return {"success": False, "error": "Neo4j未连接"}

        # 构造提示词，让DeepSeek从回答中提取结构化知识
        extract_prompt = (
            "你是一个音乐知识图谱的信息抽取专家。请从以下问答对中提取有价值的音乐知识，"
            "以JSON格式返回。如果问答内容不包含可提取的音乐知识（如闲聊、无关话题），"
            "请返回空JSON {\"nodes\": [], \"relations\": []}。\n\n"
            "节点类型只能是: Singer, Song, Album, Tag\n"
            "关系类型只能是: SING, IN_ALBUM, BELONG_TO_ALBUM, COLLABORATE, USE\n\n"
            "节点属性说明:\n"
            "- Singer: 必须有 singer_name（歌手名）\n"
            "- Song: 必须有 song_name（歌曲名），可选 album（专辑）、publish_year（年份）、language（语言）\n"
            "- Album: 必须有 name（专辑名），可选 publish_year（年份）\n"
            "- Tag: 必须有 name（标签名，如流派、风格）\n\n"
            "关系说明:\n"
            "- SING: 歌手->歌曲（谁唱了什么歌）\n"
            "- IN_ALBUM: 歌曲->专辑（歌曲收录在哪个专辑）\n"
            "- BELONG_TO_ALBUM: 歌手->专辑（歌手拥有哪个专辑）\n"
            "- COLLABORATE: 歌手->歌手（合作关系）\n"
            "- USE: 歌曲->标签（歌曲属于什么风格/流派）\n\n"
            "返回格式示例:\n"
            '{"nodes": [{"label": "Singer", "props": {"singer_name": "周杰伦"}}, '
            '{"label": "Song", "props": {"song_name": "晴天", "album": "叶惠美", "publish_year": "2003"}}], '
            '"relations": [{"type": "SING", "from_label": "Singer", "from_name": "周杰伦", '
            '"to_label": "Song", "to_name": "晴天"}]}\n\n'
            f"用户问题: {question}\n"
            f"回答内容: {answer}\n\n"
            "请提取知识并返回JSON（不要包含任何其他文字）:"
        )

        try:
            result = self.ask_deepseek_json(question, extract_prompt)
            if not result:
                print("[知识回写] DeepSeek未返回有效JSON，跳过")
                return {"success": False, "error": "未提取到知识"}

            nodes = result.get("nodes", [])
            relations = result.get("relations", [])

            if not nodes and not relations:
                print("[知识回写] 无可提取的音乐知识")
                return {"success": False, "error": "无音乐知识"}

            # 写入Neo4j
            write_result = self._write_knowledge_to_neo4j(nodes, relations)
            print(f"[知识回写] 成功写入 {write_result['nodes_written']} 个节点, {write_result['relations_written']} 条关系")
            return {"success": True, **write_result}

        except Exception as e:
            print(f"[知识回写] 提取或写入失败: {e}")
            return {"success": False, "error": str(e)}

    def _write_knowledge_to_neo4j(self, nodes, relations):
        """将提取的节点和关系写入Neo4j，使用MERGE避免重复"""
        nodes_written = 0
        relations_written = 0

        # 节点标签与唯一标识属性的映射
        label_key_map = {
            "Singer": "singer_name",
            "Song": "song_name",
            "Album": "name",
            "Tag": "name"
        }

        with self.driver.session() as session:
            # 1. 写入节点
            for node in nodes:
                label = node.get("label")
                props = node.get("props", {})
                if not label or not props:
                    continue

                key_prop = label_key_map.get(label, "name")
                key_value = props.get(key_prop)
                if not key_value:
                    continue

                try:
                    # 构建属性设置语句
                    prop_sets = ", ".join(
                        f"n.{k} = ${k}" for k in props.keys()
                    )
                    cypher = f"MERGE (n:{label} {{{key_prop}: ${key_prop}}}) SET {prop_sets}"
                    session.run(cypher, props)
                    nodes_written += 1
                except Exception as e:
                    print(f"[知识回写] 节点写入失败 {label}/{key_value}: {e}")

            # 2. 写入关系
            for rel in relations:
                rel_type = rel.get("type")
                from_label = rel.get("from_label")
                from_name = rel.get("from_name")
                to_label = rel.get("to_label")
                to_name = rel.get("to_name")

                if not all([rel_type, from_label, from_name, to_label, to_name]):
                    continue

                from_key = label_key_map.get(from_label, "name")
                to_key = label_key_map.get(to_label, "name")

                try:
                    cypher = (
                        f"MATCH (a:{from_label} {{{from_key}: $from_name}}) "
                        f"MATCH (b:{to_label} {{{to_key}: $to_name}}) "
                        f"MERGE (a)-[:{rel_type}]->(b)"
                    )
                    session.run(cypher, {"from_name": from_name, "to_name": to_name})
                    relations_written += 1
                except Exception as e:
                    print(f"[知识回写] 关系写入失败 {from_name}-[{rel_type}]->{to_name}: {e}")

        return {"nodes_written": nodes_written, "relations_written": relations_written}

    def direct_cypher(self, cypher):
        """直接执行Cypher查询，仅允许读操作"""
        write_keywords = ["CREATE", "DELETE", "DROP", "SET", "MERGE", "REMOVE", "FOREACH"]
        upper_cypher = cypher.upper()
        if any(keyword in upper_cypher for keyword in write_keywords):
            return {"error": "禁止执行写操作", "status": 403}

        if not self.driver:
            return {"error": "Neo4j 未连接", "status": 500}

        try:
            with self.driver.session() as session:
                result = session.run(cypher)
                records = [dict(record) for record in result]
                return {"results": records, "status": 200}
        except Exception as e:
            return {"error": str(e), "status": 500}


def main():
    """主函数 - 测试问答引擎"""
    engine = QAEngine()

    test_questions = [
        "周杰伦演唱了哪些歌曲",
        "林俊杰有多少首歌",
        "谁演唱了《夜空中最亮的星》",
        "五月天有哪些专辑"
    ]

    for question in test_questions:
        print(f"\n{'='*50}")
        print(f"问题: {question}")
        result = engine.answer(question)
        print(f"答案: {result['answer']}")

    engine.close()


if __name__ == "__main__":
    main()
