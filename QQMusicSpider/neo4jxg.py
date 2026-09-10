from neo4j import GraphDatabase
import json
import os

# -------------------------- 配置项（请根据你的实际情况修改） --------------------------
# Neo4j连接配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")  # Neo4j服务地址，默认本地7687端口
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")                # Neo4j用户名，默认neo4j
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")             # 你设置的Neo4j密码

# music文件路径（根据你的项目结构修改，截图中文件在QQMusicSpider目录下，和items.py同级）
MUSIC_FILE_PATH = "./music"
# -----------------------------------------------------------------------------------


def process_single_record(tx, record: dict):
    """
    处理单条音乐数据：创建/合并歌手、歌曲、专辑节点，并建立关系
    :param tx: Neo4j事务对象
    :param record: 单条音乐数据（JSON解析后的字典）
    """
    # 1. 提取所有字段（兼容空值，避免KeyError）
    singer_names = record.get("singer_name", [])
    singer_ids = record.get("singer_id", [])
    singer_mids = record.get("singer_mid", [])
    
    song_name = record.get("song_name", "")
    subtitle = record.get("subtitle", "")
    album_name = record.get("album_name", "")
    song_time_public = record.get("song_time_public", "")
    song_type = record.get("song_type", 0)
    language = record.get("language", 0)
    song_id = record.get("song_id", 0)
    song_mid = record.get("song_mid", "")
    song_url = record.get("song_url", "")
    hot_comments = record.get("hot_comments", "")
    lyric = record.get("lyric", "")

    # -------------------------- 2. 处理专辑节点（Album） --------------------------
    # MERGE：存在则不创建，不存在则创建，保证去重
    tx.run(
        """
        MERGE (a:Album {album_name: $album_name})
        SET a.album_name = $album_name
        """,
        album_name=album_name
    )

    # -------------------------- 3. 处理歌曲节点（Song）+ 歌曲-专辑关系 --------------------------
    tx.run(
        """
        MERGE (s:Song {song_id: $song_id, song_mid: $song_mid})
        SET s.song_name = $song_name,
            s.subtitle = $subtitle,
            s.song_time_public = $song_time_public,
            s.song_type = $song_type,
            s.language = $language,
            s.song_url = $song_url,
            s.hot_comments = $hot_comments,
            s.lyric = $lyric
        WITH s
        MATCH (a:Album {album_name: $album_name})
        MERGE (s)-[:BELONGS_TO]->(a)
        """,
        song_id=song_id,
        song_mid=song_mid,
        song_name=song_name,
        subtitle=subtitle,
        song_time_public=song_time_public,
        song_type=song_type,
        language=language,
        song_url=song_url,
        hot_comments=hot_comments,
        lyric=lyric,
        album_name=album_name
    )

    # -------------------------- 4. 处理歌手节点（Singer）+ 歌手-歌曲关系 --------------------------
    # 处理多歌手情况（如样例中的刘欢/那英），保证歌手列表、ID列表、mid列表一一对应
    max_len = len(singer_names)
    for idx in range(max_len):
        # 按索引取对应歌手的信息，兼容列表长度不一致的情况
        singer_name = singer_names[idx]
        singer_id = singer_ids[idx] if idx < len(singer_ids) else None
        singer_mid = singer_mids[idx] if idx < len(singer_mids) else None

        tx.run(
            """
            MERGE (singer:Singer {singer_id: $singer_id, singer_mid: $singer_mid})
            SET singer.singer_name = $singer_name
            WITH singer
            MATCH (song:Song {song_id: $song_id, song_mid: $song_mid})
            MERGE (singer)-[:SING]->(song)
            """,
            singer_id=singer_id,
            singer_mid=singer_mid,
            singer_name=singer_name,
            song_id=song_id,
            song_mid=song_mid
        )


def main():
    # 1. 连接Neo4j并验证连通性
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("✅ Neo4j连接成功！")
    except Exception as e:
        print(f"❌ Neo4j连接失败：{e}")
        return

    # 2. 读取music文件并逐行处理
    try:
        with driver.session() as session:
            # 读取JSON Lines格式文件（每行一个JSON对象，对应截图中的文件格式）
            with open(MUSIC_FILE_PATH, "r", encoding="utf-8") as f:
                line_count = 0
                success_count = 0
                for line in f:
                    line = line.strip()
                    line_count += 1
                    if not line:
                        continue  # 跳过空行

                    try:
                        # 解析JSON
                        record = json.loads(line)
                        # 执行数据导入
                        session.execute_write(process_single_record, record)
                        success_count += 1
                    except json.JSONDecodeError as e:
                        print(f"⚠️ 第{line_count}行JSON解析失败：{line[:50]}...，错误：{e}")
                    except Exception as e:
                        print(f"⚠️ 第{line_count}行数据处理失败：{e}")

                print(f"\n📊 导入完成：共{line_count}行，成功{success_count}行")

    except FileNotFoundError:
        print(f"❌ 找不到文件：{MUSIC_FILE_PATH}，请检查文件路径是否正确")
    except Exception as e:
        print(f"❌ 文件读取失败：{e}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()