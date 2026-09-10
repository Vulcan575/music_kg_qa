# -*- coding: utf-8 -*-
"""生成答辩PPT - 简单版"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

def add_slide(prs, layout_idx=1):
    """添加幻灯片"""
    slide_layout = prs.slide_layouts[layout_idx]
    return prs.slides.add_slide(slide_layout)

def set_slide_bg(slide, r, g, b):
    """设置幻灯片背景色"""
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor(r, g, b)

def add_textbox(slide, left, top, width, height, text, font_size=18, bold=False,
                color=RGBColor(51, 51, 51), alignment=PP_ALIGN.LEFT, font_name="微软雅黑"):
    """添加文本框"""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.alignment = alignment
    return txBox

def add_bullet_textbox(slide, left, top, width, height, items, font_size=16,
                       color=RGBColor(51, 51, 51), font_name="微软雅黑", line_spacing=1.5):
    """添加带项目符号的文本框"""
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = item
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = font_name
        p.space_after = Pt(font_size * 0.5)
        p.level = 0
    return txBox

def add_decorated_title(slide, text, left=Inches(0.6), top=Inches(0.3),
                        width=Inches(8.8), height=Inches(0.8)):
    """添加装饰性标题（带左侧竖条）"""
    # 左侧装饰竖条
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top + Inches(0.05),
                                    Inches(0.08), height - Inches(0.1))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0, 102, 204)
    shape.line.fill.background()

    # 标题文字
    add_textbox(slide, left + Inches(0.25), top, width - Inches(0.25), height,
                text, font_size=28, bold=True, color=RGBColor(0, 51, 102))

def add_page_number(slide, num, total):
    """添加页码"""
    add_textbox(slide, Inches(8.8), Inches(7.0), Inches(1.0), Inches(0.4),
                f"{num}/{total}", font_size=10, color=RGBColor(153, 153, 153),
                alignment=PP_ALIGN.RIGHT)

def create_ppt():
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    TOTAL = 14  # 总页数

    # ========== 第1页：封面 ==========
    slide = add_slide(prs, layout_idx=6)  # 空白布局
    set_slide_bg(slide, 0, 51, 102)

    # 顶部装饰线
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0),
                                    Inches(10), Inches(0.06))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(255, 200, 50)
    shape.line.fill.background()

    # 学校信息
    add_textbox(slide, Inches(0.5), Inches(1.2), Inches(9), Inches(0.6),
                "智算工程学院  计算机科学与技术专业", font_size=16,
                color=RGBColor(180, 200, 230), alignment=PP_ALIGN.CENTER)

    # 论文题目
    add_textbox(slide, Inches(0.5), Inches(2.2), Inches(9), Inches(1.2),
                "基于知识图谱的智能问答系统", font_size=36, bold=True,
                color=RGBColor(255, 255, 255), alignment=PP_ALIGN.CENTER)

    # 副标题
    add_textbox(slide, Inches(0.5), Inches(3.5), Inches(9), Inches(0.6),
                "毕业设计答辩", font_size=20,
                color=RGBColor(200, 220, 255), alignment=PP_ALIGN.CENTER)

    # 分隔线
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(3.5), Inches(4.3),
                                    Inches(3), Inches(0.03))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(255, 200, 50)
    shape.line.fill.background()

    # 学生信息
    info_items = [
        "答辩人：郝军浩",
        "学    号：6022203153",
        "指导教师：陈淑鑫",
        "日    期：2026年6月"
    ]
    for i, item in enumerate(info_items):
        add_textbox(slide, Inches(3.0), Inches(4.7 + i * 0.45), Inches(4), Inches(0.45),
                    item, font_size=16, color=RGBColor(200, 220, 255),
                    alignment=PP_ALIGN.CENTER)

    # ========== 第2页：目录 ==========
    slide = add_slide(prs, layout_idx=6)
    set_slide_bg(slide, 245, 247, 250)
    add_decorated_title(slide, "汇报提纲")

    contents = [
        "一、研究背景与意义",
        "二、相关技术与理论基础",
        "三、系统需求分析与总体设计",
        "四、核心模块详细设计",
        "五、系统实现与测试",
        "六、总结与展望"
    ]
    for i, item in enumerate(contents):
        y = Inches(1.5 + i * 0.85)
        # 序号圆圈
        shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(1.5), y, Inches(0.5), Inches(0.5))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(0, 102, 204)
        shape.line.fill.background()
        tf = shape.text_frame
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.text = str(i + 1)
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.alignment = PP_ALIGN.CENTER
        tf.paragraphs[0].font.name = "微软雅黑"

        add_textbox(slide, Inches(2.2), y + Inches(0.05), Inches(6), Inches(0.5),
                    item, font_size=20, color=RGBColor(51, 51, 51))
    add_page_number(slide, 2, TOTAL)

    # ========== 第3页：研究背景与意义 ==========
    slide = add_slide(prs, layout_idx=6)
    set_slide_bg(slide, 245, 247, 250)
    add_decorated_title(slide, "一、研究背景与意义")

    add_textbox(slide, Inches(0.6), Inches(1.3), Inches(4.2), Inches(0.4),
                "▎研究背景", font_size=18, bold=True, color=RGBColor(0, 102, 204))
    bg_items = [
        "• 数字音乐平台普及，用户需求从简单搜索升级为知识搜索与交互体验",
        "• 传统搜索仅支持关键词匹配，无法处理复杂关联查询",
        "• AI技术空前火热，音乐数字化与AI融合趋势明显",
        "• 缺乏完整的用户权限管理和个性化交互平台"
    ]
    add_bullet_textbox(slide, Inches(0.6), Inches(1.8), Inches(4.2), Inches(2.5),
                       bg_items, font_size=14, color=RGBColor(68, 68, 68))

    add_textbox(slide, Inches(5.2), Inches(1.3), Inches(4.2), Inches(0.4),
                "▎研究意义", font_size=18, bold=True, color=RGBColor(0, 102, 204))
    sig_items = [
        "• 理论意义：探索大模型、知识图谱与用户权限在垂直领域的融合",
        "  优化实体抽取、多跳推理和安全查询技术",
        "• 实践意义：实现精准音乐知识智能问答",
        "  增加全页面音乐播放、双角色权限管控、管理员后台",
        "  知识图谱可视化等功能，构建完整体验"
    ]
    add_bullet_textbox(slide, Inches(5.2), Inches(1.8), Inches(4.2), Inches(2.5),
                       sig_items, font_size=14, color=RGBColor(68, 68, 68))

    # 国内外现状
    add_textbox(slide, Inches(0.6), Inches(4.5), Inches(9), Inches(0.4),
                "▎国内外发展现状", font_size=18, bold=True, color=RGBColor(0, 102, 204))
    status_items = [
        "• 国外：MusicBrainz等已实现百万级实体存储，大模型与KG深度融合，但缺乏中文音乐支持",
        "• 国内：主流平台开始探索KG+LLM融合，但功能单一、无独立用户体系、核心技术未开源",
        "• 本项目目标：在核心问答功能基础上，补充完整用户体系、管理员运维和前端交互等工程化功能"
    ]
    add_bullet_textbox(slide, Inches(0.6), Inches(5.0), Inches(8.8), Inches(2.0),
                       status_items, font_size=14, color=RGBColor(68, 68, 68))
    add_page_number(slide, 3, TOTAL)

    # ========== 第4页：相关技术与理论基础 ==========
    slide = add_slide(prs, layout_idx=6)
    set_slide_bg(slide, 245, 247, 250)
    add_decorated_title(slide, "二、相关技术与理论基础")

    # 六大技术卡片
    techs = [
        ("Scrapy", "高性能爬虫框架\n异步非阻塞采集\n断点续爬机制", RGBColor(46, 139, 87)),
        ("Neo4j", "图数据库\n属性图模型\nCypher查询语言", RGBColor(0, 100, 180)),
        ("DeepSeek", "国产AI大模型\n中文理解优异\nAPI接口调用", RGBColor(142, 68, 173)),
        ("Flask", "轻量Web框架\nRESTful API\nJinja2模板引擎", RGBColor(192, 57, 43)),
        ("Vue3", "前端框架\nComposition API\n响应式数据绑定", RGBColor(39, 174, 96)),
        ("SQLite", "轻量关系数据库\n文件式存储\n用户认证管理", RGBColor(211, 84, 0)),
    ]

    for i, (name, desc, color) in enumerate(techs):
        col = i % 3
        row = i // 3
        x = Inches(0.6 + col * 3.1)
        y = Inches(1.4 + row * 2.8)

        # 卡片背景
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y,
                                        Inches(2.8), Inches(2.4))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(255, 255, 255)
        shape.line.color.rgb = RGBColor(220, 220, 220)
        shape.line.width = Pt(1)

        # 顶部色条
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(2.8), Inches(0.06))
        bar.fill.solid()
        bar.fill.fore_color.rgb = color
        bar.line.fill.background()

        # 技术名称
        add_textbox(slide, x + Inches(0.15), y + Inches(0.2), Inches(2.5), Inches(0.4),
                    name, font_size=20, bold=True, color=color)
        # 描述
        add_textbox(slide, x + Inches(0.15), y + Inches(0.7), Inches(2.5), Inches(1.5),
                    desc, font_size=13, color=RGBColor(80, 80, 80))
    add_page_number(slide, 4, TOTAL)

    # ========== 第5页：系统总体架构 ==========
    slide = add_slide(prs, layout_idx=6)
    set_slide_bg(slide, 245, 247, 250)
    add_decorated_title(slide, "三、系统总体架构设计")

    # 三层架构
    layers = [
        ("应用层", "Flask后端 + Vue3前端\n智能问答 | 图谱可视化 | 热度榜单\n知识挑战 | 用户管理 | 音乐播放器",
         RGBColor(0, 102, 204), Inches(1.4)),
        ("引擎层", "知识图谱构建引擎 | 智能问答引擎 | 榜单数据引擎\n自然语言理解 | Cypher生成 | 多跳推理 | 知识回写",
         RGBColor(46, 139, 87), Inches(3.3)),
        ("数据层", "Neo4j图数据库 | SQLite关系数据库 | JSON缓存文件\n歌手/歌曲/专辑节点 | 用户/管理员表 | 热度榜单缓存",
         RGBColor(142, 68, 173), Inches(5.2)),
    ]

    for name, desc, color, y in layers:
        # 层背景
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), y,
                                        Inches(8.4), Inches(1.6))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(255, 255, 255)
        shape.line.color.rgb = color
        shape.line.width = Pt(2)

        # 层名称标签
        label = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.9), y + Inches(0.15),
                                        Inches(1.4), Inches(0.45))
        label.fill.solid()
        label.fill.fore_color.rgb = color
        label.line.fill.background()
        tf = label.text_frame
        p = tf.paragraphs[0]
        p.text = name
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.font.name = "微软雅黑"
        p.alignment = PP_ALIGN.CENTER

        # 描述
        add_textbox(slide, Inches(2.5), y + Inches(0.15), Inches(6.5), Inches(1.3),
                    desc, font_size=14, color=RGBColor(68, 68, 68))

    # 箭头指示
    for y_pos in [Inches(3.05), Inches(4.95)]:
        shape = slide.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(4.8), y_pos,
                                        Inches(0.4), Inches(0.3))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(200, 200, 200)
        shape.line.fill.background()

    add_page_number(slide, 5, TOTAL)

    # ========== 第6页：数据库设计 ==========
    slide = add_slide(prs, layout_idx=6)
    set_slide_bg(slide, 245, 247, 250)
    add_decorated_title(slide, "三、数据库设计")

    # 知识图谱本体
    add_textbox(slide, Inches(0.6), Inches(1.3), Inches(4.2), Inches(0.4),
                "▎知识图谱本体设计（5类核心节点）", font_size=16, bold=True, color=RGBColor(0, 102, 204))

    nodes = [
        ("Singer\n歌手", "mid, name, nationality,\nbirthday, fans, tags"),
        ("Song\n歌曲", "mid, name, year,\nduration, language, plays"),
        ("Album\n专辑", "mid, name, year,\nsong_count, type"),
        ("BirthDate\n出生日期", "date"),
        ("AlbumDate\n发行日期", "date"),
    ]

    for i, (name, attrs) in enumerate(nodes):
        x = Inches(0.6 + i * 1.85)
        y = Inches(1.9)
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y,
                                        Inches(1.7), Inches(1.8))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(255, 255, 255)
        shape.line.color.rgb = RGBColor(0, 102, 204)
        shape.line.width = Pt(1.5)

        add_textbox(slide, x + Inches(0.05), y + Inches(0.1), Inches(1.6), Inches(0.5),
                    name, font_size=12, bold=True, color=RGBColor(0, 102, 204),
                    alignment=PP_ALIGN.CENTER)
        add_textbox(slide, x + Inches(0.05), y + Inches(0.7), Inches(1.6), Inches(1.0),
                    attrs, font_size=10, color=RGBColor(100, 100, 100),
                    alignment=PP_ALIGN.CENTER)

    # 关系说明
    add_textbox(slide, Inches(0.6), Inches(4.0), Inches(9), Inches(0.4),
                "▎核心关系类型", font_size=16, bold=True, color=RGBColor(0, 102, 204))

    rel_items = [
        "Singer -[SING]-> Song（歌手演唱歌曲）",
        "Singer -[RELEASE]-> Album（歌手发行专辑）",
        "Singer -[HAS_BIRTH]-> BirthDate（歌手出生日期）",
        "Album -[INCLUDE]-> Song（专辑包含歌曲）",
        "Album -[HAS_DATE]-> AlbumDate（专辑发行日期）"
    ]
    add_bullet_textbox(slide, Inches(0.6), Inches(4.5), Inches(4.5), Inches(2.5),
                       rel_items, font_size=13, color=RGBColor(68, 68, 68))

    # SQLite表
    add_textbox(slide, Inches(5.5), Inches(4.0), Inches(4), Inches(0.4),
                "▎SQLite数据表", font_size=16, bold=True, color=RGBColor(0, 102, 204))

    sqlite_items = [
        "用户表：id, username, password(SHA-256),\n  created_at, is_active",
        "管理员表：id, username, password,\n  created_at, invite_code验证"
    ]
    add_bullet_textbox(slide, Inches(5.5), Inches(4.5), Inches(4), Inches(2.0),
                       sqlite_items, font_size=13, color=RGBColor(68, 68, 68))
    add_page_number(slide, 6, TOTAL)

    # ========== 第7页：数据采集与预处理 ==========
    slide = add_slide(prs, layout_idx=6)
    set_slide_bg(slide, 245, 247, 250)
    add_decorated_title(slide, "四、数据采集与预处理模块")

    # 反爬策略
    add_textbox(slide, Inches(0.6), Inches(1.3), Inches(4.2), Inches(0.4),
                "▎反爬策略设计", font_size=16, bold=True, color=RGBColor(0, 102, 204))
    anti_items = [
        "1. UserAgent轮换：维护数十个浏览器UA，随机选取",
        "2. 请求频率控制：固定下载延迟，关闭Cookie",
        "3. 请求头自动补全：针对API添加特定Header"
    ]
    add_bullet_textbox(slide, Inches(0.6), Inches(1.8), Inches(4.2), Inches(1.8),
                       anti_items, font_size=13, color=RGBColor(68, 68, 68))

    # 断点续爬
    add_textbox(slide, Inches(5.2), Inches(1.3), Inches(4.2), Inches(0.4),
                "▎断点续爬机制", font_size=16, bold=True, color=RGBColor(0, 102, 204))
    resume_items = [
        "1. 启动时从Neo4j加载已爬取的mid集合",
        "2. 爬取时自动跳过已存在的实体",
        "3. 中断后重启无需从头开始"
    ]
    add_bullet_textbox(slide, Inches(5.2), Inches(1.8), Inches(4.2), Inches(1.8),
                       resume_items, font_size=13, color=RGBColor(68, 68, 68))

    # 数据采集流程
    add_textbox(slide, Inches(0.6), Inches(3.8), Inches(9), Inches(0.4),
                "▎数据采集流程", font_size=16, bold=True, color=RGBColor(0, 102, 204))

    steps = [
        ("步骤1", "遍历歌手列表API\n获取歌手基础信息"),
        ("步骤2", "根据歌手ID调用\n歌曲列表API"),
        ("步骤3", "根据歌曲ID调用\n歌词API获取歌词"),
        ("步骤4", "Pipeline清洗后\n写入Neo4j"),
    ]
    for i, (step, desc) in enumerate(steps):
        x = Inches(0.6 + i * 2.35)
        y = Inches(4.4)
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y,
                                        Inches(2.1), Inches(1.5))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(255, 255, 255)
        shape.line.color.rgb = RGBColor(0, 102, 204)
        shape.line.width = Pt(1)

        add_textbox(slide, x + Inches(0.1), y + Inches(0.1), Inches(1.9), Inches(0.35),
                    step, font_size=14, bold=True, color=RGBColor(0, 102, 204),
                    alignment=PP_ALIGN.CENTER)
        add_textbox(slide, x + Inches(0.1), y + Inches(0.5), Inches(1.9), Inches(0.9),
                    desc, font_size=12, color=RGBColor(80, 80, 80),
                    alignment=PP_ALIGN.CENTER)

        # 箭头
        if i < 3:
            arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,
                                            x + Inches(2.1), y + Inches(0.55),
                                            Inches(0.25), Inches(0.3))
            arrow.fill.solid()
            arrow.fill.fore_color.rgb = RGBColor(0, 102, 204)
            arrow.line.fill.background()

    # 预处理
    add_textbox(slide, Inches(0.6), Inches(6.2), Inches(9), Inches(0.4),
                "▎数据预处理：数据清洗 → 实体与关系抽取 → 数据去重（MERGE语句）",
                font_size=14, color=RGBColor(68, 68, 68))
    add_page_number(slide, 7, TOTAL)

    # ========== 第8页：智能问答引擎 ==========
    slide = add_slide(prs, layout_idx=6)
    set_slide_bg(slide, 245, 247, 250)
    add_decorated_title(slide, "四、智能问答引擎模块设计")

    # 三个子模块
    modules = [
        ("自然语言理解模块", [
            "• 调用DeepSeek大模型",
            "• 少样本学习策略（3组示例）",
            "• 输出5个核心字段：",
            "  entity_type, entity_name,",
            "  relation, question_type,",
            "  properties"
        ], RGBColor(0, 102, 204)),
        ("Cypher查询生成模块", [
            "• 模板匹配优先策略",
            "• 预定义12类常用问句模板",
            "• 模板无法匹配时调用大模型",
            "• 安全校验：禁止CREATE、",
            "  DELETE、DROP、SET、",
            "  MERGE等写操作关键字"
        ], RGBColor(46, 139, 87)),
        ("多跳推理与答案生成", [
            "• 执行Cypher查询",
            "• 单跳：结果填入答案模板",
            "• 多跳：DeepSeek综合分析",
            "  生成完整自然语言答案",
            "• 知识回写：从答案中提取",
            "  新知识写入Neo4j"
        ], RGBColor(142, 68, 173)),
    ]

    for i, (name, items, color) in enumerate(modules):
        x = Inches(0.4 + i * 3.2)
        y = Inches(1.4)

        # 卡片
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y,
                                        Inches(3.0), Inches(4.0))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(255, 255, 255)
        shape.line.color.rgb = color
        shape.line.width = Pt(2)

        # 标题栏
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(3.0), Inches(0.5))
        bar.fill.solid()
        bar.fill.fore_color.rgb = color
        bar.line.fill.background()
        add_textbox(slide, x + Inches(0.1), y + Inches(0.05), Inches(2.8), Inches(0.4),
                    name, font_size=14, bold=True, color=RGBColor(255, 255, 255),
                    alignment=PP_ALIGN.CENTER)

        # 内容
        add_bullet_textbox(slide, x + Inches(0.15), y + Inches(0.6), Inches(2.7), Inches(3.2),
                           items, font_size=12, color=RGBColor(68, 68, 68))

    # 流程箭头
    for i in range(2):
        x = Inches(3.4 + i * 3.2)
        arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, x, Inches(3.2),
                                        Inches(0.25), Inches(0.3))
        arrow.fill.solid()
        arrow.fill.fore_color.rgb = RGBColor(200, 200, 200)
        arrow.line.fill.background()

    # 底部总结
    add_textbox(slide, Inches(0.6), Inches(5.8), Inches(8.8), Inches(0.8),
                "核心策略：模板匹配优先（快速、可预测、无语法错误） + 大模型兜底（灵活处理复杂查询） + 安全校验（保障数据库安全）",
                font_size=13, color=RGBColor(0, 102, 204), bold=True)
    add_page_number(slide, 8, TOTAL)

    # ========== 第9页：Web交互模块 ==========
    slide = add_slide(prs, layout_idx=6)
    set_slide_bg(slide, 245, 247, 250)
    add_decorated_title(slide, "四、Web交互模块设计")

    features = [
        ("智能问答界面", "左右分栏布局\n左侧问答主区域+对话历史\n右侧月热度榜单+图谱统计", "💬"),
        ("知识图谱可视化", "vis.js网络图渲染\n搜索实体、展开邻居节点\n拖拽缩放交互", "🔗"),
        ("国内月热度榜单", "整合QQ音乐/网易云/酷狗\n排名加权+跨平台加分算法\n综合榜+三平台Tab切换", "📊"),
        ("音乐知识挑战", "基于KG自动生成选择题\n8道题/局，连击奖励\n2×2选项网格布局", "🎮"),
        ("用户与管理员系统", "双角色权限隔离\nSHA-256密码加密\n邀请码注册管理员", "👤"),
        ("全页面音乐播放器", "登录/注册/问答/图谱页\n歌曲切换+封面旋转+歌词同步\nsessionStorage保持状态", "🎵"),
    ]

    for i, (name, desc, icon) in enumerate(features):
        col = i % 3
        row = i // 3
        x = Inches(0.5 + col * 3.1)
        y = Inches(1.4 + row * 2.8)

        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y,
                                        Inches(2.9), Inches(2.5))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(255, 255, 255)
        shape.line.color.rgb = RGBColor(220, 220, 220)
        shape.line.width = Pt(1)

        add_textbox(slide, x + Inches(0.15), y + Inches(0.15), Inches(2.6), Inches(0.4),
                    name, font_size=15, bold=True, color=RGBColor(0, 102, 204))
        add_textbox(slide, x + Inches(0.15), y + Inches(0.6), Inches(2.6), Inches(1.7),
                    desc, font_size=12, color=RGBColor(80, 80, 80))
    add_page_number(slide, 9, TOTAL)

    # ========== 第10页：系统实现效果 ==========
    slide = add_slide(prs, layout_idx=6)
    set_slide_bg(slide, 245, 247, 250)
    add_decorated_title(slide, "五、系统实现效果")

    impl_items = [
        ("用户登录与注册", "紫色渐变背景设计，密码强度校验，管理员独立入口+邀请码注册"),
        ("智能问答", "十字形布局，输入问题后显示思考状态，对话历史按时间展示"),
        ("知识图谱可视化", "vis.js渲染网络图，搜索高亮节点，展开邻居关系"),
        ("国内月热度榜单", "综合榜/QQ音乐/网易云/酷狗四Tab切换，前三名高亮"),
        ("音乐知识挑战", "8道选择题，即时反馈，连击奖励机制"),
        ("管理员后台", "用户列表、系统统计、知识图谱规模展示，用户账号管理"),
    ]

    for i, (name, desc) in enumerate(impl_items):
        col = i % 2
        row = i // 2
        x = Inches(0.5 + col * 4.8)
        y = Inches(1.4 + row * 1.8)

        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y,
                                        Inches(4.5), Inches(1.5))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(255, 255, 255)
        shape.line.color.rgb = RGBColor(220, 220, 220)

        # 序号
        num_shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, x + Inches(0.15), y + Inches(0.15),
                                            Inches(0.4), Inches(0.4))
        num_shape.fill.solid()
        num_shape.fill.fore_color.rgb = RGBColor(0, 102, 204)
        num_shape.line.fill.background()
        tf = num_shape.text_frame
        p = tf.paragraphs[0]
        p.text = str(i + 1)
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.font.name = "微软雅黑"
        p.alignment = PP_ALIGN.CENTER

        add_textbox(slide, x + Inches(0.65), y + Inches(0.15), Inches(3.7), Inches(0.35),
                    name, font_size=15, bold=True, color=RGBColor(0, 51, 102))
        add_textbox(slide, x + Inches(0.65), y + Inches(0.55), Inches(3.7), Inches(0.8),
                    desc, font_size=12, color=RGBColor(80, 80, 80))
    add_page_number(slide, 10, TOTAL)

    # ========== 第11页：系统测试 ==========
    slide = add_slide(prs, layout_idx=6)
    set_slide_bg(slide, 245, 247, 250)
    add_decorated_title(slide, "五、系统测试")

    # 功能测试
    add_textbox(slide, Inches(0.6), Inches(1.3), Inches(4.2), Inches(0.4),
                "▎功能测试（12项用例全部通过）", font_size=16, bold=True, color=RGBColor(0, 102, 204))
    func_items = [
        "✓ 用户注册/登录/退出",
        "✓ 管理员邀请码注册",
        "✓ 智能问答（单跳/多跳）",
        "✓ 知识图谱可视化搜索",
        "✓ 月热度榜单四Tab切换",
        "✓ 音乐知识挑战游戏",
        "✓ Cypher安全校验拦截",
        "✓ 知识回写功能",
    ]
    add_bullet_textbox(slide, Inches(0.6), Inches(1.8), Inches(4.2), Inches(3.5),
                       func_items, font_size=13, color=RGBColor(46, 139, 87))

    # 性能测试
    add_textbox(slide, Inches(5.2), Inches(1.3), Inches(4.2), Inches(0.4),
                "▎性能测试结果", font_size=16, bold=True, color=RGBColor(0, 102, 204))
    perf_items = [
        "• 单跳问答响应：< 3秒",
        "• 多跳问答响应：< 5秒",
        "• 图谱可视化加载：< 2秒",
        "• 榜单数据加载：< 1秒",
        "• 用户注册/登录：< 0.5秒",
        "• 知识回写耗时：< 6秒",
        "• 系统稳定性：连续运行无异常",
    ]
    add_bullet_textbox(slide, Inches(5.2), Inches(1.8), Inches(4.2), Inches(3.5),
                       perf_items, font_size=13, color=RGBColor(68, 68, 68))

    # 知识图谱规模
    add_textbox(slide, Inches(0.6), Inches(5.5), Inches(9), Inches(0.4),
                "▎知识图谱规模统计", font_size=16, bold=True, color=RGBColor(0, 102, 204))

    stats = [
        ("1,300+", "歌手"),
        ("7,700+", "歌曲"),
        ("3,000+", "专辑"),
        ("32,000+", "关系"),
    ]
    for i, (num, label) in enumerate(stats):
        x = Inches(0.8 + i * 2.3)
        y = Inches(6.0)
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y,
                                        Inches(2.0), Inches(0.9))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(0, 102, 204)
        shape.line.fill.background()
        add_textbox(slide, x + Inches(0.1), y + Inches(0.05), Inches(1.8), Inches(0.4),
                    num, font_size=20, bold=True, color=RGBColor(255, 255, 255),
                    alignment=PP_ALIGN.CENTER)
        add_textbox(slide, x + Inches(0.1), y + Inches(0.5), Inches(1.8), Inches(0.3),
                    label, font_size=12, color=RGBColor(200, 220, 255),
                    alignment=PP_ALIGN.CENTER)
    add_page_number(slide, 11, TOTAL)

    # ========== 第12页：研究工作总结 ==========
    slide = add_slide(prs, layout_idx=6)
    set_slide_bg(slide, 245, 247, 250)
    add_decorated_title(slide, "六、研究工作总结")

    summary_items = [
        ("构建音乐领域知识图谱", "Scrapy采集QQ音乐多源数据，实体识别与关系抽取后导入Neo4j，构建包含1300+歌手、7700+歌曲、3000+专辑、32000+关系的知识图谱，设计断点续爬机制"),
        ("设计智能问答引擎", "模板匹配优先+大模型生成策略，结合DeepSeek实现自然语言理解、意图识别、Cypher查询生成和多跳推理，实现知识回写机制动态扩展图谱"),
        ("开发完整Web交互系统", "基于Flask+Vue3构建，实现智能问答、知识图谱可视化、国内月热度榜单、音乐知识挑战、双角色权限体系、全页面音乐播放器"),
        ("全面系统测试", "12项功能测试全部通过，性能指标均达预期，验证系统可靠性和稳定性"),
    ]

    for i, (title, desc) in enumerate(summary_items):
        y = Inches(1.4 + i * 1.4)
        # 序号
        num_shape = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.6), y + Inches(0.1),
                                            Inches(0.5), Inches(0.5))
        num_shape.fill.solid()
        num_shape.fill.fore_color.rgb = RGBColor(0, 102, 204)
        num_shape.line.fill.background()
        tf = num_shape.text_frame
        p = tf.paragraphs[0]
        p.text = str(i + 1)
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.font.name = "微软雅黑"
        p.alignment = PP_ALIGN.CENTER

        add_textbox(slide, Inches(1.3), y, Inches(8), Inches(0.4),
                    title, font_size=16, bold=True, color=RGBColor(0, 51, 102))
        add_textbox(slide, Inches(1.3), y + Inches(0.4), Inches(8), Inches(0.9),
                    desc, font_size=13, color=RGBColor(80, 80, 80))
    add_page_number(slide, 12, TOTAL)

    # ========== 第13页：研究不足与展望 ==========
    slide = add_slide(prs, layout_idx=6)
    set_slide_bg(slide, 245, 247, 250)
    add_decorated_title(slide, "六、研究不足与展望")

    deficiencies = [
        ("知识图谱覆盖范围有限", "主要覆盖华语主流音乐，小众/欧美/日韩音乐覆盖不足，数据来源单一（仅QQ音乐）",
         "扩展网易云音乐、酷狗音乐等数据源，丰富图谱内容"),
        ("知识回写准确率待提升", "依赖DeepSeek提取知识，可能存在错误写入风险",
         "设置知识筛查机制，人工审核后入库"),
        ("并发处理能力有限", "基于Flask开发服务器运行，并发能力有限",
         "部署到Gunicorn/uWSGI生产级服务器"),
        ("前端架构可优化", "采用CDN引入Vue3方式，未使用Vite和单文件组件",
         "迁移到标准Vue3项目架构，提升开发效率和可维护性"),
        ("创意性功能不够丰富", "音乐知识挑战题型单一",
         "增加更多题型和创意功能，与时俱进"),
    ]

    for i, (title, problem, solution) in enumerate(deficiencies):
        y = Inches(1.3 + i * 1.15)
        # 不足
        add_textbox(slide, Inches(0.6), y, Inches(0.8), Inches(0.3),
                    f"不足{i+1}", font_size=11, bold=True, color=RGBColor(192, 57, 43))
        add_textbox(slide, Inches(1.4), y, Inches(3.5), Inches(0.3),
                    title, font_size=13, bold=True, color=RGBColor(51, 51, 51))
        add_textbox(slide, Inches(1.4), y + Inches(0.3), Inches(3.5), Inches(0.6),
                    problem, font_size=11, color=RGBColor(120, 120, 120))
        # 展望
        add_textbox(slide, Inches(5.5), y, Inches(0.8), Inches(0.3),
                    f"展望", font_size=11, bold=True, color=RGBColor(46, 139, 87))
        add_textbox(slide, Inches(6.3), y, Inches(3.3), Inches(0.8),
                    solution, font_size=11, color=RGBColor(80, 80, 80))

    add_page_number(slide, 13, TOTAL)

    # ========== 第14页：致谢 ==========
    slide = add_slide(prs, layout_idx=6)
    set_slide_bg(slide, 0, 51, 102)

    # 顶部装饰线
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0),
                                    Inches(10), Inches(0.06))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(255, 200, 50)
    shape.line.fill.background()

    add_textbox(slide, Inches(0.5), Inches(2.5), Inches(9), Inches(1.0),
                "感谢各位老师的聆听与指导！", font_size=32, bold=True,
                color=RGBColor(255, 255, 255), alignment=PP_ALIGN.CENTER)

    # 分隔线
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(3.5), Inches(3.8),
                                    Inches(3), Inches(0.03))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(255, 200, 50)
    shape.line.fill.background()

    add_textbox(slide, Inches(0.5), Inches(4.2), Inches(9), Inches(0.6),
                "答辩人：郝军浩    指导教师：陈淑鑫", font_size=18,
                color=RGBColor(200, 220, 255), alignment=PP_ALIGN.CENTER)

    add_textbox(slide, Inches(0.5), Inches(5.0), Inches(9), Inches(0.6),
                "敬请各位老师批评指正", font_size=16,
                color=RGBColor(180, 200, 230), alignment=PP_ALIGN.CENTER)

    # 保存
    output_path = r"d:\毕业设计试验\music_kg_qa\答辩PPT.pptx"
    prs.save(output_path)
    print(f"PPT已保存至: {output_path}")

if __name__ == "__main__":
    create_ppt()
