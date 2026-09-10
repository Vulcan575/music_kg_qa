# -*- coding: utf-8 -*-
"""
Flask Web应用后端
提供RESTful API接口
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import sqlite3
import re
import os
from datetime import datetime
import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from qa_engine.qa_engine import QAEngine
from kg_builder.kg_builder import KnowledgeGraphBuilder
from chart_fetcher import get_hot_chart
import config

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-temp-secret-key-for-dev')
CORS(app)

# 初始化引擎
qa_engine = QAEngine()
kg_builder = None

# 数据库初始化
DB_FILE = Path(__file__).parent / "history.db"

# 管理员邀请码（注册管理员时需要提供）
ADMIN_INVITE_CODE = os.getenv('ADMIN_INVITE_CODE', 'music2024')


def init_db():
    """初始化SQLite数据库"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # 问答历史表
    c.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            cypher TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 用户表（兼容已有表结构）
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # 管理员表
    c.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 尝试给 users 表添加 status 列（如果不存在）
    try:
        c.execute("ALTER TABLE users ADD COLUMN status TEXT DEFAULT 'active'")
    except Exception:
        pass  # 列已存在，忽略

    conn.commit()
    conn.close()
    print("数据库初始化成功（含用户表和管理员表）")


# ====================== 密码强度校验 ======================
def is_valid_password(password):
    """要求：8-16位，必须包含数字、字母和特殊符号"""
    if not (8 <= len(password) <= 16):
        return False, "密码长度必须在8到16位之间"
    if not re.search(r"[a-zA-Z]", password):
        return False, "密码必须包含字母"
    if not re.search(r"[0-9]", password):
        return False, "密码必须包含数字"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "密码必须包含特殊符号"
    return True, "密码符合要求"


# ====================== 页面路由 ======================

@app.route("/")
def index():
    """首页 - 已登录跳转问答页，未登录跳转登录页"""
    if 'username' in session:
        return redirect(url_for('qa_page'))
    return redirect(url_for('login_page'))


@app.route("/login")
def login_page():
    """登录页面"""
    if 'username' in session:
        return redirect(url_for('qa_page'))
    return render_template("login.html")


@app.route("/register")
def register_page():
    """注册页面"""
    return render_template("register.html")


@app.route("/qa")
def qa_page():
    """智能问答主页面（受保护的路由）"""
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template("index.html")


@app.route("/graph")
def graph():
    """图谱可视化页"""
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template("graph.html")


# ====================== 用户认证接口 ======================

@app.route("/api/register", methods=["POST"])
def register():
    """注册接口"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not username or not password:
        return jsonify({"success": False, "message": "账号和密码不能为空"}), 400

    # 检查密码确认
    if password != confirm_password:
        return jsonify({"success": False, "message": "两次输入的密码不一致"}), 400

    # 检查密码强度
    is_valid, msg = is_valid_password(password)
    if not is_valid:
        return jsonify({"success": False, "message": msg}), 400

    # 检查用户名是否已存在
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "该账号已被注册，请更换账号"}), 400

    # 存储用户
    c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "注册成功，请登录"}), 201


@app.route("/api/login", methods=["POST"])
def login():
    """登录接口"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password, status FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()

    if row and row[0] == password:
        if len(row) > 1 and row[1] == 'disabled':
            return jsonify({"success": False, "message": "该账号已被禁用，请联系管理员"}), 403
        session['username'] = username
        return jsonify({"success": True, "message": "登录成功", "redirect": url_for('qa_page')})
    return jsonify({"success": False, "message": "账号或密码错误"}), 401


@app.route("/api/logout", methods=["POST"])
def logout():
    """退出登录"""
    session.pop('username', None)
    return jsonify({"success": True, "redirect": url_for('login_page')})


@app.route("/api/user/info")
def user_info():
    """获取当前用户信息"""
    if 'username' in session:
        return jsonify({"logged_in": True, "username": session['username']})
    return jsonify({"logged_in": False, "username": None})


# ====================== 管理员页面路由 ======================

@app.route("/admin/login")
def admin_login_page():
    """管理员登录页面"""
    if 'admin' in session:
        return redirect(url_for('admin_dashboard'))
    return render_template("admin_login.html")


@app.route("/admin/register")
def admin_register_page():
    """管理员注册页面"""
    return render_template("admin_register.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    """管理员仪表盘（受保护）"""
    if 'admin' not in session:
        return redirect(url_for('admin_login_page'))
    return render_template("admin_dashboard.html")


# ====================== 管理员认证接口 ======================

@app.route("/api/admin/register", methods=["POST"])
def admin_register():
    """管理员注册接口"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    invite_code = data.get('invite_code')

    if not username or not password:
        return jsonify({"success": False, "message": "账号和密码不能为空"}), 400

    # 验证邀请码
    if invite_code != ADMIN_INVITE_CODE:
        return jsonify({"success": False, "message": "邀请码错误，无法注册管理员"}), 400

    # 检查密码确认
    if password != confirm_password:
        return jsonify({"success": False, "message": "两次输入的密码不一致"}), 400

    # 检查密码强度
    is_valid, msg = is_valid_password(password)
    if not is_valid:
        return jsonify({"success": False, "message": msg}), 400

    # 检查管理员名是否已存在
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM admins WHERE username = ?", (username,))
    if c.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "该管理员账号已存在"}), 400

    c.execute("INSERT INTO admins (username, password) VALUES (?, ?)", (username, password))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "管理员注册成功，请登录"}), 201


@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    """管理员登录接口"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT password FROM admins WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()

    if row and row[0] == password:
        session['admin'] = username
        return jsonify({"success": True, "message": "登录成功", "redirect": url_for('admin_dashboard')})
    return jsonify({"success": False, "message": "管理员账号或密码错误"}), 401


@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    """管理员退出登录"""
    session.pop('admin', None)
    return jsonify({"success": True, "redirect": url_for('admin_login_page')})


@app.route("/api/admin/info")
def admin_info():
    """获取当前管理员信息"""
    if 'admin' in session:
        return jsonify({"logged_in": True, "username": session['admin']})
    return jsonify({"logged_in": False, "username": None})


# ====================== 管理员管理接口 ======================

@app.route("/api/admin/users")
def admin_get_users():
    """获取所有用户列表"""
    if 'admin' not in session:
        return jsonify({"error": "未授权"}), 401

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, username, role, status, create_time FROM users ORDER BY create_time DESC")
    rows = c.fetchall()
    conn.close()

    users = [dict(row) for row in rows]
    return jsonify({"users": users})


@app.route("/api/admin/delete_user", methods=["POST"])
def admin_delete_user():
    """删除用户"""
    if 'admin' not in session:
        return jsonify({"error": "未授权"}), 401

    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({"success": False, "message": "用户名不能为空"}), 400

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    deleted = c.rowcount
    conn.close()

    if deleted > 0:
        return jsonify({"success": True, "message": f"用户 {username} 已删除"})
    return jsonify({"success": False, "message": "用户不存在"}), 404


@app.route("/api/admin/toggle_user", methods=["POST"])
def admin_toggle_user():
    """切换用户状态（启用/禁用）"""
    if 'admin' not in session:
        return jsonify({"error": "未授权"}), 401

    data = request.get_json()
    username = data.get('username')

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT status FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"success": False, "message": "用户不存在"}), 404

    new_status = 'disabled' if row[0] == 'active' else 'active'
    c.execute("UPDATE users SET status = ? WHERE username = ?", (new_status, username))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"用户 {username} 已{'禁用' if new_status == 'disabled' else '启用'}", "new_status": new_status})


@app.route("/api/admin/stats")
def admin_stats():
    """获取系统统计数据"""
    if 'admin' not in session:
        return jsonify({"error": "未授权"}), 401

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # 总用户数
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]

    # 今日新增用户
    c.execute("SELECT COUNT(*) FROM users WHERE DATE(create_time) = DATE('now')")
    today_users = c.fetchone()[0]

    # 总问答次数
    c.execute("SELECT COUNT(*) FROM history")
    total_qa = c.fetchone()[0]

    # 管理员数量
    c.execute("SELECT COUNT(*) FROM admins")
    total_admins = c.fetchone()[0]

    conn.close()

    return jsonify({
        "total_users": total_users,
        "today_users": today_users,
        "total_qa": total_qa,
        "total_admins": total_admins
    })


# ====================== 问答接口 ======================

@app.route("/api/qa", methods=["POST"])
def qa():
    """
    问答接口
    请求: {"question": "问题内容"}
    返回: {"answer": "答案", "cypher": "查询语句", "graph_data": {...}}
    """
    data = request.get_json()
    question = data.get("question", "")

    if not question:
        return jsonify({"error": "问题不能为空"}), 400

    try:
        # 调用问答引擎
        result = qa_engine.answer(question)

        # 保存到历史记录
        save_history(question, result["answer"], result.get("cypher", ""))

        # 异步回写知识到Neo4j（不阻塞用户响应）
        try:
            kb_result = qa_engine.extract_knowledge_to_neo4j(question, result["answer"])
            if kb_result.get("success"):
                print(f"[知识回写] 新增 {kb_result.get('nodes_written',0)} 节点, {kb_result.get('relations_written',0)} 关系")
        except Exception as kb_err:
            print(f"[知识回写] 回写失败（不影响用户）: {kb_err}")

        return jsonify({
            "answer": result["answer"],
            "cypher": result.get("cypher", ""),
            "graph_data": result.get("graph_data", {"nodes": [], "edges": []})
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ====================== 图谱接口 ======================

@app.route("/api/graph/stats", methods=["GET"])
def graph_stats():
    """获取图谱统计信息"""
    global kg_builder

    if kg_builder is None:
        kg_builder = KnowledgeGraphBuilder()
        kg_builder.connect()

    try:
        stats = kg_builder.get_stats()
        response = jsonify({
            "singers": stats.get("singers", 0),
            "songs": stats.get("songs", 0),
            "relations": stats.get("relations", 0)
        })
        response.headers["Cache-Control"] = "no-store"
        return response
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/graph/search", methods=["GET"])
def graph_search():
    """搜索图谱实体"""
    keyword = request.args.get("keyword", "")

    if not keyword:
        return jsonify({"error": "关键词不能为空"}), 400

    global kg_builder

    if kg_builder is None:
        kg_builder = KnowledgeGraphBuilder()
        kg_builder.connect()

    try:
        results = kg_builder.search_entity(keyword)
        return jsonify({"results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/graph/neighbors", methods=["GET"])
def graph_neighbors():
    """获取实体邻居"""
    name = request.args.get("name", "")

    if not name:
        return jsonify({"error": "实体名称不能为空"}), 400

    global kg_builder

    if kg_builder is None:
        kg_builder = KnowledgeGraphBuilder()
        kg_builder.connect()

    try:
        neighbors = kg_builder.get_neighbors(name)
        return jsonify({"neighbors": neighbors})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/graph/nodes", methods=["GET"])
def graph_nodes():
    """获取图谱节点和关系，用于可视化预览"""
    try:
        limit = int(request.args.get("limit", 50))
    except ValueError:
        limit = 50

    try:
        kg = get_kg_builder()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    try:
        # 1. 直接查询所有节点
        query = """
        MATCH (n)
        WHERE exists(n.name) OR exists(n.song_name) OR exists(n.singer_name)
        RETURN id(n) AS id, labels(n)[0] AS type,
               coalesce(n.name, n.song_name, n.singer_name) AS name
        LIMIT $limit
        """
        with kg.driver.session() as sess:
            # 1. 先查询关系，找到需要显示的节点 ID
            rel_query = """
            MATCH (a)-[r]->(b)
            RETURN id(a) AS from, id(b) AS to, type(r) AS relation
            LIMIT $rel_limit
            """
            rel_result = sess.run(rel_query, rel_limit=limit * 3)
            raw_edges = [dict(record) for record in rel_result]

            # 2. 查询这些关系中涉及的节点
            node_ids = set()
            for record in raw_edges:
                node_ids.add(record["from"])
                node_ids.add(record["to"])

            if node_ids:
                node_query = """
                MATCH (n)
                WHERE id(n) IN $ids AND (exists(n.name) OR exists(n.song_name) OR exists(n.singer_name))
                RETURN id(n) AS id, labels(n)[0] AS type,
                       coalesce(n.name, n.song_name, n.singer_name) AS name
                """
                result = sess.run(node_query, ids=list(node_ids))
                nodes = [dict(record) for record in result]
            else:
                # 如果没有关系，则退回查询普通节点
                result = sess.run(query, limit=limit)
                nodes = [dict(record) for record in result]

            # 关系中文映射
            relation_map = {
                "SING": "演唱",
                "BELONG_TO_ALBUM": "所属专辑",
                "IN_ALBUM": "所属专辑",
                "COLLABORATE": "合作",
                "USE": "使用",
                "DEFAULT": "关联"
            }
            edges = [
                {
                    "from": record["from"],
                    "to": record["to"],
                    "label": record["relation"],
                    "relation": relation_map.get(record.get("relation"), relation_map["DEFAULT"])
                }
                for record in raw_edges
            ]

        # 颜色映射
        color_map = {
            "Singer": "#667eea",
            "Song": "#4ecdc4",
            "Album": "#ffa502",
            "Tag": "#f6bb42",
            "Composer": "#e74c3c",
            "Genre": "#9b59b6",
            "Lyricist": "#f39c12",
            "Music": "#2ecc71",
            "Artist": "#1abc9c"
        }

        graph_nodes = [
            {
                "id": record["id"],
                "label": record["name"],
                "type": record.get("type", ""),
                "group": record.get("type", "Unknown"),
                "color": color_map.get(record.get("type", ""), "#95a5a6"),
                "size": 25
            }
            for record in nodes
        ]

        return jsonify({
            "success": True,
            "nodes": graph_nodes,
            "edges": edges,
            "data": {
                "nodes": graph_nodes,
                "edges": edges
            }
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ====================== 历史记录接口 ======================

@app.route("/api/history", methods=["GET"])
def get_history():
    """获取问答历史"""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM history ORDER BY created_at DESC LIMIT 50")
        rows = c.fetchall()
        conn.close()

        history = [dict(row) for row in rows]
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/history/clear", methods=["POST"])
def clear_history():
    """清空历史记录"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM history")
        conn.commit()
        conn.close()
        return jsonify({"message": "历史记录已清空"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ====================== 辅助函数 ======================

def save_history(question, answer, cypher):
    """保存问答记录"""
    try:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            "INSERT INTO history (question, answer, cypher) VALUES (?, ?, ?)",
            (question, answer, cypher)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"保存历史记录失败: {e}")


def get_kg_builder():
    """返回一个已连接的图谱构建器实例"""
    global kg_builder
    if kg_builder is None:
        kg_builder = KnowledgeGraphBuilder()
    if kg_builder.driver is None:
        if not kg_builder.connect():
            raise RuntimeError("无法连接到Neo4j数据库，请检查配置")
    return kg_builder


# ====================== 健康检查 ======================

@app.route("/api/health", methods=["GET"])
def health():
    """健康检查"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})


def create_app():
    """创建Flask应用"""
    init_db()
    return app


@app.route("/api/chart/hot", methods=["GET"])
def api_chart_hot():
    try:
        chart = get_hot_chart()
        return jsonify(chart)
    except Exception as e:
        return jsonify({"error": str(e), "combined": [], "qq_hot": [], "netease_hot": []}), 500


@app.route("/api/game/quiz", methods=["GET"])
def api_game_quiz():
    import random
    try:
        kg = get_kg_builder()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    try:
        with kg.driver.session() as session:
            singer_songs = session.run("""
                MATCH (s:Singer)-[r:SING]->(song:Song)
                WHERE s.singer_name IS NOT NULL AND coalesce(song.song_name, song.name) IS NOT NULL
                WITH s.singer_name AS singer, collect(DISTINCT coalesce(song.song_name, song.name)) AS songs
                WHERE size(songs) >= 1
                RETURN singer, songs[0] AS song
                LIMIT 50
            """)
            pairs = [(r["singer"], r["song"]) for r in singer_songs if r["singer"] and r["song"]]

            all_songs = session.run("""
                MATCH (song:Song)
                WHERE coalesce(song.song_name, song.name) IS NOT NULL
                RETURN DISTINCT coalesce(song.song_name, song.name) AS song
                LIMIT 500
            """)
            song_pool = [r["song"] for r in all_songs if r["song"]]

            if len(pairs) < 4:
                return jsonify({"error": "知识图谱数据不足，请先爬取更多数据"}), 400

            random.shuffle(pairs)
            questions = []

            for singer, song in pairs:
                wrong_songs = [s for s in song_pool if s != song]
                if len(wrong_songs) < 3:
                    continue
                wrong = random.sample(wrong_songs, 3)
                options = wrong + [song]
                random.shuffle(options)

                questions.append({
                    "type": "singer_song",
                    "question": f"歌手「{singer}」演唱了以下哪首歌曲？",
                    "options": options,
                    "answer": song
                })
                if len(questions) >= 5:
                    break

            album_songs = session.run("""
                MATCH (song:Song)-[r:BELONGS_TO]->(album:Album)
                WHERE coalesce(album.album_name, album.name, '') <> '' AND coalesce(song.song_name, song.name) IS NOT NULL
                WITH coalesce(album.album_name, album.name) AS album, collect(DISTINCT coalesce(song.song_name, song.name)) AS songs
                WHERE size(songs) >= 1
                RETURN album, songs[0] AS song
                LIMIT 30
            """)
            album_pairs = [(r["album"], r["song"]) for r in album_songs if r["album"] and r["song"]]

            if len(album_pairs) >= 4:
                random.shuffle(album_pairs)
                for album, song in album_pairs:
                    wrong_songs2 = [s for s in song_pool if s != song]
                    if len(wrong_songs2) < 3:
                        continue
                    wrong2 = random.sample(wrong_songs2, 3)
                    options2 = wrong2 + [song]
                    random.shuffle(options2)

                    questions.append({
                        "type": "album_song",
                        "question": f"专辑「{album}」中包含以下哪首歌曲？",
                        "options": options2,
                        "answer": song
                    })
                    if len(questions) >= 8:
                        break

            random.shuffle(questions)
            return jsonify({"questions": questions, "total": len(questions)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    init_db()

    flask_config = config.FLASK_CONFIG
    app.run(
        host=flask_config["HOST"],
        port=flask_config["PORT"],
        debug=flask_config["DEBUG"]
    )
