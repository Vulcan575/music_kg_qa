from QQMusicSpider.items import MusicItem
from scrapy import Request
import json
import re
import os
from scrapy.spiders import Spider
from neo4j import GraphDatabase  # 新增Neo4j导入
# DmozSpider
class QQMusicSpider(Spider):
    # 根据地区area参数筛选歌手，-100:全部，200:内地,2:港台，5:欧美，4:日本，3:韩国，6:其他
    name = "qqmusic"
    handle_httpstatus_list = [500]
    # 新增Neo4j配置（和pipelines.py保持一致）
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
    # 存储已爬的歌手mid和歌曲mid（实例变量，在__init__中初始化）
    crawled_singer_mids = None
    crawled_song_mids = None

    start_urls = [
        'https://u.y.qq.com/cgi-bin/musicu.fcg?data=%7B%22singerList%22%3A%7B%22module%22%3A%22Music.SingerListServer' \
        '%22%2C%22method%22%3A%22get_singer_list%22%2C%22param%22%3A%7B%22area%22%3A{area}%2C%22sex%22%3A-100%2C%22genr' \
        'e%22%3A-100%2C%22index%22%3A-100%2C%22sin%22%3A{index}%2C%22cur_page%22%3A{cur_page}%7D%7D%7D'
    ]
    # 以下原有url定义不变，省略...
    song_list_url = "https://u.y.qq.com/cgi-bin/musicu.fcg?data=%7B%22comm%22%3A%7B%22ct%22%3A24%2C%22cv%22%3A0%7D%2C%22singerSongList%22%3A%7B%22method%22%3A%22GetSingerSongList%22%2C%22param%22%3A%7B%22order%22%3A1%2C%22singerMid%22%3A%22{singer_mid}%22%2C%22begin%22%3A{begin}%2C%22num%22%3A{num}%7D%2C%22module%22%3A%22musichall.song_list_server%22%7D%7D"
    lyric_url = "https://c.y.qq.com/lyric/fcgi-bin/fcg_query_lyric_yqq.fcg?nobase64=1&musicid={song_id}&format=json"
    referer = "https://y.qq.com/n/yqq/song/{song_mid}.html"
    comment_url = 'https://c.y.qq.com/base/fcgi-bin/fcg_global_comment_h5.fcg?biztype=1&topid={song_id}&cmd=8&pagenum={pagenum}&pagesize={pagesize}'
    song_url = "https://y.qq.com/n/yqq/song/{song_mid}.html"
    # 记录爬虫当前爬取的歌曲数量
    music_num = 0

    def __init__(self, *args, **kwargs):
        """初始化爬虫，加载已爬数据实现断点续爬"""
        super(QQMusicSpider, self).__init__(*args, **kwargs)
        self.crawled_singer_mids = set()
        self.crawled_song_mids = set()
        self._load_crawled_data()

    def _load_crawled_data(self):
        """从Neo4j和本地文件加载已爬数据"""
        # 1. 先从Neo4j加载
        try:
            driver = GraphDatabase.driver(
                self.NEO4J_URI,
                auth=(self.NEO4J_USER, self.NEO4J_PASSWORD)
            )
            driver.verify_connectivity()
            self.logger.info("✅ 成功连接Neo4j，开始加载已爬数据")
            with driver.session() as session:
                # 加载已爬歌手mid（兼容Singer标签）
                singer_res = session.run("MATCH (s:Singer) RETURN s.singer_mid AS mid")
                for record in singer_res:
                    mid = record.get("mid")
                    if mid:
                        self.crawled_singer_mids.add(mid)
                # 加载已爬歌曲mid（兼容Song和Music标签）
                song_res = session.run("MATCH (m) WHERE m:Song OR m:Music RETURN m.song_mid AS mid")
                for record in song_res:
                    mid = record.get("mid")
                    if mid:
                        self.crawled_song_mids.add(mid)
            driver.close()
            self.logger.info(f"✅ Neo4j已爬数据：歌手{len(self.crawled_singer_mids)}个，歌曲{len(self.crawled_song_mids)}首")
        except Exception as e:
            self.logger.warning(f"❌ Neo4j连接失败：{e}，将从本地文件加载")

        # 2. 从本地music文件补充
        self._load_crawled_from_music_file()
        self.logger.info(f"🔁 断点续爬就绪：已爬歌手{len(self.crawled_singer_mids)}个，歌曲{len(self.crawled_song_mids)}首")

    def _load_crawled_from_music_file(self):
        """从本地 music 文件加载已爬 song_mid 及 singer_mid"""
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "music")
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        song_mid = data.get('song_mid')
                        if song_mid:
                            self.crawled_song_mids.add(song_mid)
                        singer_mid_list = data.get('singer_mid')
                        if isinstance(singer_mid_list, list):
                            self.crawled_singer_mids.update(singer_mid_list)
                    except Exception:
                        continue
            self.logger.info(f"✅ 本地music文件补充：歌手{len(self.crawled_singer_mids)}个，歌曲{len(self.crawled_song_mids)}首")
        except Exception as e:
            self.logger.warning(f"读取本地 music 文件失败：{e}")

    @staticmethod
    def _setting_int(settings, key, default=0):
        """Scrapy -s overrides are strings; normalize to int before arithmetic."""
        value = settings.get(key, default)
        return int(value)

    # 原有start_requests不变，省略...
    def start_requests(self):
        singer_page_num = self._setting_int(self.settings, 'SINGER_PAGE_NUM')
        singer_page_size = self._setting_int(self.settings, 'SINGER_PAGE_SIZE')
        for i in range(1, singer_page_num + 1):
            # 港台歌手
            request = Request(
                self.start_urls[0].format(index=singer_page_size * (i - 1), cur_page=i, area=2),
                callback=self.parse_singer)
            yield request
            # 内地歌手
            request = Request(
                self.start_urls[0].format(index=singer_page_size * (i - 1), cur_page=i, area=200),
                callback=self.parse_singer)
            yield request

    # 关键修改：parse_singer中跳过已爬歌手
    def parse_singer(self, response):
        """爬取歌手，跳过已爬的singer_mid"""
        singer_list = json.loads(response.text).get('singerList').get('data').get('singerlist')
        if not singer_list:
            return
        song_page_num = self._setting_int(self.settings, 'SONG_PAGE_NUM')
        song_page_size = self._setting_int(self.settings, 'SONG_PAGE_SIZE')
        for singer in singer_list:
            singer_mid = singer.get('singer_mid')
            # 核心判断：如果歌手已爬，直接跳过
            if not singer_mid or singer_mid in self.crawled_singer_mids:
                self.logger.info(f"⏭️  跳过已爬歌手：{singer.get('singer_name')}（mid：{singer_mid}）")
                continue
            # 未爬歌手，继续发起歌曲请求
            singer_id = singer.get('singer_id')
            singer_name = singer.get('singer_name')
            singer_pic = singer.get('singer_pic')
            for page in range(0, song_page_num):
                request = Request(
                    self.song_list_url.format(singer_mid=singer_mid, begin=page * song_page_size, num=song_page_size),
                    callback=self.parse_song)
                yield request

    # 关键修改：parse_song中跳过已爬歌曲
    def parse_song(self, response):
        """爬取歌曲，跳过已爬的song_mid"""
        song_list = json.loads(response.text).get('singerSongList').get('data').get("songList")
        if not song_list:
            return
        for song in song_list:
            songInfo = song.get('songInfo')
            song_mid = songInfo.get('mid')
            # 核心判断：如果歌曲已爬，直接跳过
            if not song_mid or song_mid in self.crawled_song_mids:
                self.logger.info(f"⏭️  跳过已爬歌曲：{songInfo.get('title')}（mid：{song_mid}）")
                continue
            # 未爬歌曲，继续构造Item并请求评论/歌词
            music_item = MusicItem()
            singer_name = []
            singer_id = []
            singer_mid_list = []
            for singer in songInfo.get('singer'):
                singer_name.append(singer.get("name"))
                singer_id.append(singer.get("id"))
                singer_mid_list.append(singer.get("mid"))
            music_item["singer_name"] = singer_name
            music_item["song_name"] = songInfo.get('title')
            music_item["subtitle"] = songInfo.get('subtitle')
            music_item["album_name"] = songInfo.get('album').get('name')
            music_item["singer_id"] = singer_id
            music_item["singer_mid"] = singer_mid_list
            music_item["song_time_public"] = songInfo.get('time_public')
            music_item["song_type"] = songInfo.get('type')
            music_item["language"] = songInfo.get('language')
            music_item["song_id"] = songInfo.get('id')
            music_item["song_mid"] = song_mid
            music_item["song_url"] = self.song_url.format(song_mid=song_mid)
            # 请求评论
            request = Request(
                url=self.comment_url.format(song_id=music_item["song_id"], pagenum=0, pagesize=20),
                callback=self.parse_comments,
                meta={'music_item': music_item}
            )
            yield request

    # 以下parse_comments、process_lyric、parse_lyric完全不变，省略...
    def parse_comments(self, response):
        music_item = response.meta.get('music_item')
        hot_comments = 'null'
        if response.status == 200:
            try:
                hot_comment_data = json.loads(response.text).get('hot_comment') or {}
                hot_comment_list = hot_comment_data.get('commentlist') or []
                if hot_comment_list:
                    hot_comments = [
                        {
                            'comment_name': comment.get('nick'),
                            'comment_text': comment.get('rootcommentcontent')
                        }
                        for comment in hot_comment_list
                    ]
            except Exception:
                hot_comments = 'null'
        music_item['hot_comments'] = hot_comments
        # 请求歌词需要加上referer
        request = Request(url=self.lyric_url.format(song_id=music_item["song_id"]),
                          callback=self.parse_lyric,
                          meta={'music_item': music_item})
        request.headers['referer'] = self.referer.format(song_mid=music_item["song_mid"])
        yield request

    def process_lyric(self, lyric):
        re_lyric = re.findall(r'[[0-9]+&#[0-9]+;[0-9]+&#[0-9]+;[0-9]+].*', lyric)
        if re_lyric:
            lyric = re_lyric[0]
            lyric = lyric.replace("&#32;", " ")
            lyric = lyric.replace("&#40;", "(")  # ✅ 补充lyric.，调用字符串方法
            lyric = lyric.replace("&#41;", ")")
            lyric = lyric.replace("&#45;", "-")
            lyric = lyric.replace("&#10;", "")
            lyric = lyric.replace("&#38;apos&#59;", "'")
            result = []
            for sentence in re.split(u"[[0-9]+&#[0-9]+;[0-9]+&#[0-9]+;[0-9]+]", lyric):
                if sentence.strip() != "":
                    result.append(sentence)
            return "\\n".join(result)
        else:
            lyric = lyric.replace("&#32;", " ")
            lyric = lyric.replace("&#40;", "(")
            lyric = lyric.replace("&#41;", ")")
            lyric = lyric.replace("&#45;", "-")
            lyric = lyric.replace("&#10;", "\\n")
            lyric = lyric.replace("&#38;apos&#59;", "'")
            return lyric

    def parse_lyric(self, response):
        music_item = response.meta.get('music_item')
        response_dict = json.loads(response.text)
        if response_dict["retcode"] == 0:
            raw_lyric = response_dict["lyric"]
            lyric = self.process_lyric(raw_lyric)
            music_item["lyric"] = lyric

        # 爬取成功后立即记录 song_mid，避免同一次爬虫中重复再次请求同歌
        song_mid = music_item.get('song_mid')
        if song_mid:
            self.crawled_song_mids.add(song_mid)

        self.music_num += 1
        self.logger.info(f"成功爬取第{self.music_num}条歌曲：{music_item['song_name']}")
        yield music_item