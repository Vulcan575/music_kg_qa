# 🎵 音乐领域知识图谱智能问答系统

> 基于 **Neo4j 知识图谱** + **DeepSeek 大模型** 的音乐领域智能问答系统
> 打通「数据采集 → 图谱构建 → 语义理解 → 智能问答 → 可视化」完整链路

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.10-blue" alt="Python">
  <img src="https://img.shields.io/badge/Flask-2.3.3-green" alt="Flask">
  <img src="https://img.shields.io/badge/Neo4j-4.4-008CC1" alt="Neo4j">
  <img src="https://img.shields.io/badge/Scrapy-2.11-orange" alt="Scrapy">
  <img src="https://img.shields.io/badge/Vue-3-42b883" alt="Vue">
  <img src="https://img.shields.io/badge/license-学习研究用-lightgrey" alt="License">
</p>

---

## 📖 项目简介

本项目是一个面向音乐领域的知识图谱问答（KBQA）系统。针对通用大模型在垂直领域**事实性差、易幻觉、缺乏结构化推理能力**的问题，系统以 Neo4j 图数据库承载音乐领域结构化知识，通过**「模板匹配 + 大模型意图识别」双轨机制**将自然语言问句翻译为 Cypher 查询，实现可解释、可追溯的精准问答；当图谱无法覆盖时，自动降级到大模型开放问答，保证召回率。

系统已在本地图谱上完成实测，覆盖 **21,869 个实体节点**与 **32,650 条关系**，支持单跳查询、多跳推理、属性查询、计数查询等典型问答场景。

---

## ✨ 功能特性

### 🤖 智能问答

| 能力 | 说明 | 示例问句 |
|---|---|---|
| **单跳查询** | 歌手 → 歌曲 | 周杰伦演唱了哪些歌曲？ |
| **反向查询** | 歌曲 → 歌手 | 《晴天》是谁唱的？ |
| **属性查询** | 歌曲 → 专辑 | 《晴天》收录在哪张专辑？ |
| **计数查询** | 聚合统计 | 周杰伦有多少首歌？ |
| **多跳推理** | 歌手 → 歌曲 → 专辑 | 周杰伦有哪些专辑？ |
| **关系查询** | 歌手 → 歌手 | 周杰伦和谁合作过？ |
| **开放问答** | 图谱未覆盖时由大模型兜底 | 周杰伦是谁？ |

### 📊 知识图谱可视化

- **力导向布局**展示实体关系网络，支持缩放与拖拽
- **节点点击**查看详情，**关键词搜索**定位实体
- 支持歌手 / 歌曲 / 专辑 / 标签等多类实体的差异化着色
- 问答结果**实时渲染**为子图，直观呈现推理路径

### 🎧 其他功能

- **音乐播放器** —— 内置播放控制、歌词滚动、音量调节
- **国内月热度榜** —— 聚合 QQ 音乐 / 网易云 / 酷狗三平台榜单（带本地缓存）
- **音乐知识小游戏** —— 基于图谱数据自动生成选择题
- **问答历史** —— SQLite 持久化，支持查看与清空
- **用户与后台** —— 注册登录、密码强度校验、管理员看板、用户启停用管理

---

## 🏗️ 系统架构

系统采用经典**三层架构**，各层职责清晰、可独立演进：

```
┌─────────────────────────────────────────────────────────────┐
│  应用层  Application Layer                                   │
│  ┌───────────────────┐  ┌────────────────────────────────┐  │
│  │  Vue 3 单页前端    │  │  Flask RESTful API（30 个路由） │  │
│  │  问答 / 图谱 / 后台 │  │  鉴权 · 会话 · 参数校验          │  │
│  └───────────────────┘  └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│  引擎层  Engine Layer                                        │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐   │
│  │  爬虫引擎     │ │  图谱构建器   │ │  问答引擎           │   │
│  │  Scrapy      │ │  kg_builder  │ │  NLU → Cypher → 答案│   │
│  └──────────────┘ └──────────────┘ └────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│  数据层  Data Layer                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐   │
│  │  Neo4j       │ │  SQLite      │ │  NDJSON 原始数据    │   │
│  │  知识图谱     │ │  用户/历史    │ │  爬虫产出           │   │
│  └──────────────┘ └──────────────┘ └────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔬 核心技术实现

### 1️⃣ 双轨问答机制（核心设计）

传统 KBQA 方案或依赖纯规则模板（**泛化差**），或完全交给大模型生成 Cypher（**易幻觉、不可控**）。本系统采用**双轨互补**的降级策略：

```
用户提问
   │
   ▼
┌──────────────────────────────────────────┐
│ 第一轨：正则模板匹配（低延迟 · 高准确）      │
│ 15 条领域句式模板 → 直接映射 Cypher 模板    │
└──────────────────────────────────────────┘
   │ 未命中
   ▼
┌──────────────────────────────────────────┐
│ 第二轨：DeepSeek 意图识别（高泛化）         │
│ 问句 → 结构化意图 {实体类型, 实体, 关系,     │
│        问题类型} → 映射 Cypher 模板         │
│ ⚠ 仅当意图能映射到已有模板时才采纳，         │
│   避免大模型臆造出无法执行的查询              │
└──────────────────────────────────────────┘
   │ 仍无法处理
   ▼
┌──────────────────────────────────────────┐
│ 兜底一：图谱实体模糊匹配                     │
│ 返回候选实体列表，引导用户澄清                │
├──────────────────────────────────────────┤
│ 兜底二：大模型开放问答                       │
│ 脱离图谱，直接由 DeepSeek 生成自然语言回答     │
└──────────────────────────────────────────┘
```

**设计要点**：第二轨设置了一道**可执行性校验** —— 只有当大模型输出的意图三元组
`(实体类型, 关系类型, 问题类型)` 能命中已注册的 Cypher 模板时才采纳该意图；否则判定为
「模型只识别出实体、未识别出关系」（典型如「XX是谁」），继续下沉到开放问答。
这一约束把大模型的输出空间收敛到**可执行查询的子集**，在保留泛化能力的同时规避了幻觉查询。

### 2️⃣ 知识图谱本体设计

**6 类实体 · 7 类关系**：

| 实体类型 | 说明 | 关键属性 |
|---|---|---|
| `Singer` | 歌手 | singer_name, genre, country |
| `Song` | 歌曲 | song_name, duration, publish_year |
| `Album` | 专辑 | name, publish_year |
| `Tag` | 标签 | name |
| `Lyrics` | 歌词 | content, language |
| `Music` | 音乐条目 | song_name |

| 关系类型 | 语义 | 方向 |
|---|---|---|
| `SING` | 演唱 | Singer → Song |
| `BELONG_TO` | 属于 | Song → Singer |
| `IN_ALBUM` | 收录于 | Song → Album |
| `BELONG_TO_ALBUM` | 属于专辑 | Album → Singer |
| `COLLABORATE` | 合作 | Singer → Singer |
| `COMPOSE` | 包含歌词 | Song → Lyrics |
| `USE` | 使用标签 | Song → Tag |

### 3️⃣ 知识回写（图谱自增长）

问答过程本身也是**知识获取**过程：系统在回答用户问题后，异步从「问题 + 答案」文本中
抽取三元组并写回 Neo4j，使图谱随使用不断扩充。写回为**非阻塞**执行，不影响响应延迟。

### 4️⃣ 安全设计

- **Cypher 写操作拦截** —— 高级用户的直接 Cypher 查询通道会做安全检查，禁止 `CREATE` /
  `DELETE` / `MERGE` / `SET` 等写操作，保障数据安全
- **密码强度校验** —— 8–16 位，强制包含字母、数字、特殊符号
- **角色分离** —— 普通用户与管理员分表存储，管理员注册需邀请码
- **凭据外置** —— 所有密钥通过 `.env` 注入，不硬编码进代码

---

## 🛠️ 技术栈

| 层次 | 技术选型 |
|---|---|
| **后端框架** | Flask 2.3 + Flask-CORS |
| **图数据库** | Neo4j 4.4（Cypher 查询语言） |
| **关系数据库** | SQLite（用户、问答历史） |
| **爬虫框架** | Scrapy 2.11 |
| **大模型** | DeepSeek Chat API |
| **前端** | Vue 3（CDN）+ 原生 CSS + 力导向图布局 |
| **模板引擎** | Jinja2 |
| **配置管理** | python-dotenv |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Neo4j 4.4+（需提前启动服务）
- DeepSeek API Key（[申请地址](https://platform.deepseek.com/)）

### 1. 克隆项目

```bash
git clone https://github.com/Vulcan575/music_kg_qa.git
cd music_kg_qa
```

### 2. 安装依赖

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `web_app/.env.example` 为 `web_app/.env`，填入你的真实配置：

```bash
cp web_app/.env.example web_app/.env
```

```ini
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=你的Neo4j密码
DEEPSEEK_API_KEY=sk-你的密钥
FLASK_SECRET_KEY=随机字符串
ADMIN_INVITE_CODE=管理员注册邀请码
```

> ⚠️ `.env` 已被 `.gitignore` 排除，**请勿将真实密钥提交到仓库**。

### 4. 启动 Neo4j

确保 Neo4j 服务已启动，默认监听 `bolt://localhost:7687`。

### 5. 构建知识图谱

```bash
python kg_builder/kg_builder.py
```

### 6. 启动服务

```bash
cd web_app
python app.py
```

后端默认运行在 `http://localhost:5000`，直接访问即可（页面由 Flask 渲染）。

### 7. （可选）重新采集数据

```bash
cd QQMusicSpider
scrapy crawl qqmusic
```

---

## 📡 API 接口

### 问答

```http
POST /api/qa
Content-Type: application/json

{ "question": "周杰伦演唱了哪些歌曲？" }
```

```json
{
  "answer": "与'周杰伦'相关的结果：\n  1. 晴天\n  2. 七里香\n  ...",
  "cypher": "MATCH (s:Singer {singer_name: $entity})-[:SING]->(song:Song) ...",
  "graph_data": {
    "nodes": [{ "id": 0, "label": "周杰伦", "type": "Singer", "size": 30 }],
    "edges": [{ "from": 0, "to": 1, "relation": "SING" }]
  }
}
```

### 图谱

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/graph/stats` | GET | 图谱统计（实体数 / 关系数） |
| `/api/graph/search?keyword=周杰伦` | GET | 按关键词搜索实体 |
| `/api/graph/neighbors?id=<node_id>` | GET | 查询邻居节点 |
| `/api/graph/nodes` | GET | 获取图谱节点数据 |

### 用户与历史

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/register` | POST | 用户注册 |
| `/api/login` | POST | 用户登录 |
| `/api/logout` | POST | 退出登录 |
| `/api/user/info` | GET | 当前用户信息 |
| `/api/history` | GET | 问答历史列表 |
| `/api/history/clear` | POST | 清空问答历史 |
| `/api/health` | GET | 健康检查 |

### 管理员

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/admin/register` | POST | 管理员注册（需邀请码） |
| `/api/admin/login` | POST | 管理员登录 |
| `/api/admin/users` | GET | 用户列表 |
| `/api/admin/toggle_user` | POST | 启用 / 停用用户 |
| `/api/admin/delete_user` | POST | 删除用户 |
| `/api/admin/stats` | GET | 后台统计看板 |

### 其他

| 接口 | 方法 | 说明 |
|---|---|---|
| `/api/chart/hot` | GET | 国内月热度榜（三平台聚合） |
| `/api/game/quiz` | GET | 生成音乐知识选择题 |

---

## 📁 项目结构

```
music_kg_qa/
├── config.py                  # 统一配置（Neo4j / DeepSeek / Flask / 本体定义）
├── requirements.txt           # Python 依赖
├── .gitignore
├── 启动系统.bat               # Windows 一键启动脚本
│
├── QQMusicSpider/             # 【数据层】Scrapy 爬虫
│   ├── QQMusicSpider/
│   │   ├── spiders/
│   │   │   ├── singer_spider.py    # 歌手列表爬虫
│   │   │   └── music_spider.py     # 歌曲详情爬虫
│   │   ├── items.py / pipelines.py / middlewares.py
│   │   └── settings.py
│   ├── neo4jxg.py             # 爬取数据直连 Neo4j 导入
│   └── music                  # 原始爬取数据（NDJSON）
│
├── kg_builder/                # 【引擎层】知识图谱构建
│   └── kg_builder.py          # 数据清洗 · 去重 · 三元组抽取 · 批量导入
│
├── qa_engine/                 # 【引擎层】问答引擎
│   └── qa_engine.py           # NLU · Cypher 生成 · 答案生成 · 知识回写
│
└── web_app/                   # 【应用层】Flask Web 应用
    ├── app.py                 # 30 个 RESTful 路由
    ├── chart_fetcher.py       # 三平台热度榜聚合
    ├── .env.example           # 环境变量模板
    ├── templates/             # 7 个页面（Jinja2 + Vue3）
    │   ├── index.html         # 问答主页
    │   ├── graph.html         # 图谱可视化
    │   ├── login.html / register.html
    │   └── admin_*.html       # 管理员登录 / 注册 / 看板
    └── static/
        └── css/style.css
```

---

## 📈 图谱规模与性能

### 实测数据规模

| 实体类型 | 数量 |
|---|---|
| Music | 9,789 |
| Song | 7,658 |
| Album | 3,067 |
| Singer | 1,350 |
| Tag | 5 |
| **合计** | **21,869** |

| 关系类型 | 数量 |
|---|---|
| SING（演唱） | 24,989 |
| BELONGS_TO（属于） | 7,643 |
| USE（使用标签） | 12 |
| BELONG_TO_ALBUM | 3 |
| IN_ALBUM | 2 |
| COLLABORATE（合作） | 1 |
| **合计** | **32,650** |

### 响应性能

| 测试场景 | 样本数 | 平均响应时间 | 最大响应时间 |
|---|---|---|---|
| 单跳查询（模板匹配） | 100 次 | 0.5 s | 1.2 s |
| 计数查询（模板匹配） | 50 次 | 0.6 s | 1.4 s |
| 多跳查询（模板匹配） | 50 次 | 1.4 s | 2.8 s |
| 开放问答（大模型） | 50 次 | 2.5 s | 6.2 s |
| 图谱统计 | 50 次 | 0.3 s | 0.8 s |

> 模板匹配路径完全**不调用大模型**，纯图数据库查询，因此延迟显著低于开放问答路径。

---

## ⚠️ 注意事项

1. **本仓库不含音频文件** —— 项目中的音乐播放器需自备音频资源（版权原因未纳入版本控制），
   可放入 `web_app/static/` 目录供播放器读取。
2. **Neo4j 需独立安装** —— 本项目不包含图数据库本体，请自行安装并启动 Neo4j 4.4+。
3. **需要 DeepSeek API Key** —— 开放问答与第二轨意图识别依赖大模型，未配置 Key 时系统
   仍可通过模板匹配路径回答领域内的常见问题。
4. **爬虫仅用于学习交流** —— QQ 音乐爬虫请遵守相关网站的服务条款与法律法规。
5. **图谱数据分布** —— 当前采集的语料以华语流行歌手为主，部分关系（如 `COLLABORATE`）
   数据较稀疏，可能影响对应查询的召回。

---

## 📝 配套文档

项目内置毕设文档与演示材料的生成脚本：

```bash
python generate_chapters.py    # 生成六章论文文档
python generate_ppt.py         # 生成答辩 PPT
```

---

## 📚 参考文献

1. IFPI. (2024). *Global Music Report 2024*.
2. DeepSeek-AI. (2024). *DeepSeek-V3 Technical Report*.
3. Webber, J. (2019). *Graph Databases* (2nd ed.). O'Reilly Media.
4. 刘知远等. (2021). *知识图谱导论*. 高等教育出版社.

---

## 📄 许可证

本项目仅供**学习与研究**使用。
