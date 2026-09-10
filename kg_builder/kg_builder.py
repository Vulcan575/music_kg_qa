# -*- coding: utf-8 -*-
"""
知识图谱构建模块
负责将爬取后的音乐数据清洗并导入Neo4j数据库
"""

# ========== 放在文件最开头 ==========
import sys
import os
import json
from pathlib import Path
from neo4j import GraphDatabase
# 把项目根目录加入Python搜索路径，解决找不到config的问题
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# ==================================
import config

LANGUAGE_MAP = {
    0: "中文",
    1: "英文",
    2: "粤语",
    3: "日语",
    4: "韩语",
    5: "其他"
}

class KnowledgeGraphBuilder:
    """知识图谱构建器"""

    def __init__(self):
        """初始化Neo4j连接"""
        self.driver = None
        self.config = config.NEO4J_CONFIG

    def connect(self):
        """连接到Neo4j数据库"""
        try:
            self.driver = GraphDatabase.driver(
                self.config["URI"],
                auth=(self.config["USER"], self.config["PASSWORD"])
            )
            with self.driver.session() as session:
                session.run("RETURN 1 AS test")
                print("Neo4j 连接成功")
            return True
        except Exception as e:
            print(f"Neo4j 连接失败: {e}")
            print("请检查 config.py 中 NEO4J_CONFIG 的 URI/USER/PASSWORD 是否正确。")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
            print("Neo4j 连接已关闭")

    def create_constraints(self):
        """创建约束和索引"""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Singer) REQUIRE s.singer_mid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (song:Song) REQUIRE song.song_mid IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (a:Album) REQUIRE a.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE",
        ]

        with self.driver.session() as session:
            for c in constraints:
                try:
                    session.run(c)
                    print(f"约束创建成功: {c}")
                except Exception as e:
                    print(f"约束创建失败: {e}")

    def parse_publish_year(self, publish_date):
        """从发布时间文本中提取年份"""
        if not publish_date:
            return None
        if isinstance(publish_date, int):
            return publish_date
        if isinstance(publish_date, str):
            publish_date = publish_date.strip()
            if len(publish_date) >= 4 and publish_date[:4].isdigit():
                return int(publish_date[:4])
        return None

    def load_json_data(self, json_file):
        """读取JSON数组或JSONL文件"""
        data = []
        with open(json_file, 'r', encoding='utf-8') as f:
            text = f.read().strip()

        if not text:
            return data

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return [data]
            return data
        except json.JSONDecodeError:
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return data

    def get_record_value(self, raw_record, keys, default=None):
        """从原始记录里按优先级获取字段值"""
        for key in keys:
            if key in raw_record and raw_record[key] not in (None, "", "null"):
                return raw_record[key]
        return default

    def normalize_song_record(self, raw_record):
        """清洗单条歌曲记录"""
        singers = []
        singer_names = self.get_record_value(raw_record, [
            "singer_name", "singerName", "singers", "artist_name", "artistName"
        ], [])
        singer_mids = self.get_record_value(raw_record, [
            "singer_mid", "singerMid", "artist_mid", "artistMid"
        ], [])
        singer_ids = self.get_record_value(raw_record, [
            "singer_id", "singerId", "artist_id", "artistId"
        ], [])

        if isinstance(singer_names, str):
            singer_names = [singer_names]
        if isinstance(singer_mids, str):
            singer_mids = [singer_mids]
        if isinstance(singer_ids, int):
            singer_ids = [singer_ids]
        if isinstance(singer_ids, str):
            singer_ids = [singer_ids]

        for idx, name in enumerate(singer_names or []):
            if not name:
                continue
            singer_mid = None
            if idx < len(singer_mids) and singer_mids[idx]:
                singer_mid = singer_mids[idx]
            elif idx < len(singer_ids) and singer_ids[idx]:
                singer_mid = singer_ids[idx]
            singers.append({
                "name": str(name).strip(),
                "singer_mid": str(singer_mid).strip() if singer_mid else str(name).strip()
            })

        if not singers and singer_ids:
            for singer_id in singer_ids:
                singers.append({
                    "name": str(singer_id).strip(),
                    "singer_mid": str(singer_id).strip()
                })

        song_mid = self.get_record_value(raw_record, [
            "song_mid", "songMid", "song_id", "songId", "song_id", "songName", "song_name"
        ])
        if isinstance(song_mid, list):
            song_mid = song_mid[0] if song_mid else None

        song_name = self.get_record_value(raw_record, [
            "song_name", "songName", "name", "title"
        ], "")
        album_name = self.get_record_value(raw_record, [
            "album_name", "albumName", "album", "albumname"
        ], "未知专辑")

        language_code = self.get_record_value(raw_record, [
            "language", "song_language", "lang", "language_code"
        ])
        language = LANGUAGE_MAP.get(int(language_code), "未知") if language_code is not None and str(language_code).isdigit() else "未知"

        tags = []
        if language and language != "未知":
            tags.append(language)
        song_type = self.get_record_value(raw_record, ["song_type", "type", "genre"], None)
        if song_type is not None:
            tags.append(f"类型{song_type}")

        lyric = self.get_record_value(raw_record, [
            "lyric", "lyrics", "lyric_text", "lyricContent"
        ], None)
        if lyric in ("null", ""):
            lyric = None

        return {
            "singers": singers,
            "song_name": str(song_name).strip(),
            "song_mid": str(song_mid).strip() if song_mid else str(song_name).strip(),
            "album_name": str(album_name).strip() or "未知专辑",
            "publish_year": self.parse_publish_year(self.get_record_value(raw_record, [
                "song_time_public", "publish_time", "publish_date", "release_date"
            ])),
            "language": language,
            "lyric": lyric,
            "tags": tags,
        }

    def import_song(self, song_data):
        """导入歌曲节点、专辑节点、歌手关系以及标签"""
        cypher = """
        MERGE (song:Song {song_mid: $song_mid})
        SET song.name = $song_name,
            song.album = $album_name,
            song.publish_year = $publish_year,
            song.language = $language,
            song.lyric = $lyric
        WITH song
        MERGE (album:Album {name: $album_name})
        SET album.publish_year = $publish_year
        MERGE (song)-[:IN_ALBUM]->(album)
        WITH song, album
        UNWIND $singers AS singer_info
        MERGE (s:Singer {singer_mid: singer_info.singer_mid})
        SET s.name = singer_info.name
        MERGE (s)-[:SING]->(song)
        MERGE (s)-[:BELONG_TO_ALBUM]->(album)
        WITH song, collect(s) AS singer_nodes
        WHERE size(singer_nodes) > 1
        UNWIND range(0, size(singer_nodes) - 2) AS i
        UNWIND range(i + 1, size(singer_nodes) - 1) AS j
        MERGE (singer_nodes[i])-[:COLLABORATE]-(singer_nodes[j])
        """

        with self.driver.session() as session:
            session.run(
                cypher,
                song_mid=song_data.get("song_mid", ""),
                song_name=song_data.get("song_name", ""),
                album_name=song_data.get("album_name", "未知专辑"),
                publish_year=song_data.get("publish_year"),
                language=song_data.get("language", "未知"),
                lyric=song_data.get("lyric", None),
                singers=song_data.get("singers", [])
            )

            tags = song_data.get("tags", [])
            if tags:
                tag_query = """
                MATCH (song:Song {song_mid: $song_mid})
                WITH song
                UNWIND $tags AS tag_name
                MERGE (t:Tag {name: tag_name})
                MERGE (song)-[:USE]->(t)
                """
                session.run(tag_query, song_mid=song_data.get("song_mid", ""), tags=tags)

    def import_from_json(self, json_file):
        """从JSON文件或JSONL文件批量导入数据"""
        print(f"开始导入数据文件: {json_file}")
        songs = self.load_json_data(json_file)

        print(f"共 {len(songs)} 条歌曲记录")
        if not songs:
            print("没有发现待导入的歌曲记录。")
            return

        for i, raw_record in enumerate(songs):
            song_data = self.normalize_song_record(raw_record)
            self.import_song(song_data)
            if (i + 1) % 100 == 0:
                print(f"已导入 {i + 1} 条记录...")

        print("数据导入完成")

    def get_stats(self):
        """获取图谱统计信息"""
        queries = {
            "singers": "MATCH (s:Singer) RETURN count(s) AS count",
            "songs": "MATCH (s:Song) RETURN count(s) AS count",
            "relations": "MATCH ()-[r]->() RETURN count(r) AS count"
        }

        stats = {}
        with self.driver.session() as session:
            for name, query in queries.items():
                result = session.run(query)
                stats[name] = result.single()["count"]

        return stats

    def search_entity(self, name):
        """搜索实体（兼容不同属性名：name, singer_name, song_name）"""
        query = """
        MATCH (n)
        WHERE n.name CONTAINS $name
           OR n.singer_name CONTAINS $name
           OR n.song_name CONTAINS $name
           OR n.album_name CONTAINS $name
        RETURN labels(n)[0] AS type,
               coalesce(n.name, n.singer_name, n.song_name, n.album_name) AS name
        LIMIT 10
        """
        with self.driver.session() as session:
            result = session.run(query, name=name)
            return [dict(record) for record in result]

    def get_neighbors(self, name):
        """获取实体的邻居节点（兼容不同属性名）"""
        query = """
        MATCH (n)
        WHERE n.name = $name OR n.singer_name = $name OR n.song_name = $name OR n.album_name = $name
        MATCH (n)-[r]-(m)
        RETURN labels(n)[0] AS type1,
               coalesce(n.name, n.singer_name, n.song_name, n.album_name) AS name1,
               type(r) AS relation,
               labels(m)[0] AS type2,
               coalesce(m.name, m.singer_name, m.song_name, m.album_name) AS name2
        """
        with self.driver.session() as session:
            result = session.run(query, name=name)
            return [dict(record) for record in result]


def main():
    """主函数"""
    builder = KnowledgeGraphBuilder()

    if not builder.connect():
        return

    builder.create_constraints()

    # 爬虫产出的原始数据（JSONL），位于 QQMusicSpider/music
    raw_file = Path(__file__).parent.parent / "QQMusicSpider" / "music"
    if raw_file.exists():
        builder.import_from_json(raw_file)
    else:
        # 路径不存在时必须显式报错：静默跳过会让人误以为"导入成功但图谱是空的"
        print(f"[错误] 未找到爬虫原始数据：{raw_file}")
        print("       请先运行爬虫采集数据（scrapy crawl qqmusic），或确认该文件是否存在。")
        builder.close()
        return

    stats = builder.get_stats()
    print("\n=== 图谱统计 ===")
    for key, value in stats.items():
        print(f"{key}: {value}")

    builder.close()


if __name__ == "__main__":
    main()
