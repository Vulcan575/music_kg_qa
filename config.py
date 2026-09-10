# -*- coding: utf-8 -*-
"""
系统配置文件
请填写以下配置信息
"""

from dotenv import load_dotenv
import os

# 加载根目录的.env配置文件
load_dotenv()

# ==================== Neo4j 图数据库配置 ====================
NEO4J_CONFIG = {
    "URI": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    "USER": os.getenv("NEO4J_USER", "neo4j"),
    # 请通过 .env 配置 NEO4J_PASSWORD（参见 web_app/.env.example）
    "PASSWORD": os.getenv("NEO4J_PASSWORD", ""),
    "DATABASE": os.getenv("NEO4J_DATABASE", "neo4j")
}

# ==================== DeepSeek 大模型配置 ====================
DEEPSEEK_CONFIG = {
    # 请通过 .env 配置 DEEPSEEK_API_KEY（参见 web_app/.env.example）
    "API_KEY": os.getenv("DEEPSEEK_API_KEY", ""),
    "BASE_URL": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    "MODEL": os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    "TEMPERATURE": 0.3,
    "MAX_TOKENS": 1024,
    "TIMEOUT": 30
}

# ==================== Flask Web服务配置 ====================
FLASK_CONFIG = {
    "HOST": "0.0.0.0",
    "PORT": 5000,
    "DEBUG": True
}

# ==================== 爬虫配置 ====================
SPIDER_CONFIG = {
    "SINGER_PAGE_NUM": 40,
    "SINGER_PAGE_SIZE": 80,
    "SONG_PAGE_NUM": 15,
    "SONG_PAGE_SIZE": 100,
    "DOWNLOAD_DELAY": 0.5
}

# ==================== 知识图谱本体配置 ====================
GRAPH_SCHEMA = {
    "entities": [
        {"label": "Singer", "name": "歌手", "properties": ["name", "genre", "country"]},
        {"label": "Song", "name": "歌曲", "properties": ["name", "album", "duration", "publish_year"]},
        {"label": "Album", "name": "专辑", "properties": ["name", "publish_year"]},
        {"label": "Tag", "name": "标签", "properties": ["name"]},
        {"label": "Lyrics", "name": "歌词", "properties": ["content", "language"]},
        {"label": "Review", "name": "评论", "properties": ["content", "user", "praise"]}
    ],
    "relations": [
        {"type": "SING", "name": "演唱", "start": "Singer", "end": "Song"},
        {"type": "BELONG_TO", "name": "属于", "start": "Song", "end": "Singer"},
        {"type": "COLLABORATE", "name": "合作", "start": "Singer", "end": "Singer"},
        {"type": "COMPOSE", "name": "包含歌词", "start": "Song", "end": "Lyrics"},
        {"type": "USE", "name": "使用标签", "start": "Song", "end": "Tag"},
        {"type": "IN_ALBUM", "name": "收录于", "start": "Song", "end": "Album"},
        {"type": "BELONG_TO_ALBUM", "name": "属于专辑", "start": "Album", "end": "Singer"}
    ]
}
