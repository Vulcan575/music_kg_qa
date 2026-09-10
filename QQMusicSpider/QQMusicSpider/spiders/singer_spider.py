from QQMusicSpider.items import SingerItem
from scrapy import Request
from scrapy.spiders import Spider
from scrapy.exceptions import CloseSpider
import json
import re
from datetime import date


class QQMusicSingerSpider(Spider):
    name = "qqmusic_singer"

    # Avoid writing unrelated files via existing music pipelines for this spider.
    custom_settings = {
        "ITEM_PIPELINES": {},
        "FEED_EXPORT_ENCODING": "utf-8",
    }

    singer_list_url = (
        "https://u.y.qq.com/cgi-bin/musicu.fcg?data="
        "%7B%22singerList%22%3A%7B%22module%22%3A%22Music.SingerListServer%22%2C"
        "%22method%22%3A%22get_singer_list%22%2C%22param%22%3A%7B%22area%22%3A-100%2C"
        "%22sex%22%3A-100%2C%22genre%22%3A-100%2C%22index%22%3A-100%2C%22sin%22%3A{index}%2C"
        "%22cur_page%22%3A{cur_page}%7D%7D%7D"
    )

    singer_detail_url = (
        "https://c.y.qq.com/v8/fcg-bin/fcg_v8_singer_detail_cp.fcg"
        "?singerid={singer_id}&order=listen&begin=0&num=1&exstatus=1&utf8=1&format=json"
    )

    def __init__(self, keyword=None, max_pages=50, page_size=80, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not keyword:
            raise ValueError("Missing required argument: keyword (e.g. -a keyword=周杰伦)")
        self.keyword = keyword
        self.max_pages = int(max_pages)
        self.page_size = int(page_size)
        self._seen_mid = set()

    def start_requests(self):
        yield self._build_page_request(1)

    def _build_page_request(self, page):
        return Request(
            self.singer_list_url.format(index=self.page_size * (page - 1), cur_page=page),
            callback=self.parse_singer_page,
            cb_kwargs={"page": page},
        )

    def parse_singer_page(self, response, page):
        payload = json.loads(response.text)
        singer_list = payload.get("singerList", {}).get("data", {}).get("singerlist", [])

        matched = False
        for singer in singer_list:
            singer_name = singer.get("singer_name", "")
            singer_mid = singer.get("singer_mid")
            if self.keyword not in singer_name:
                continue
            if singer_mid in self._seen_mid:
                continue

            self._seen_mid.add(singer_mid)
            matched = True
            singer_id = singer.get("singer_id") or ""
            base_item = {
                "singer_id": singer_id,
                "singer_mid": singer_mid or "",
                "singer_name": singer_name or "",
                "singer_pic": singer.get("singer_pic") or "",
                "singer_country": singer.get("country") or "",
                "singer_genre": singer.get("genre") or "",
                "singer_index": singer.get("index") or "",
            }
            yield Request(
                self.singer_detail_url.format(singer_id=singer_id),
                callback=self.parse_singer_detail,
                meta={"base_item": base_item},
                dont_filter=True,
            )

        if matched:
            return

        if page >= self.max_pages or not singer_list:
            raise CloseSpider("singer_not_found")

        yield self._build_page_request(page + 1)

    @staticmethod
    def _extract_birth_year(text):
        if not text:
            return None

        m = re.search(r"(19\d{2}|20\d{2})年出生", text)
        if m:
            return int(m.group(1))

        m = re.search(r"([零一二三四五六七八九]{2})年出生", text)
        if m:
            cn_map = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
            two = m.group(1)
            yy = cn_map.get(two[0], -1) * 10 + cn_map.get(two[1], -1)
            if yy >= 0:
                # Singer bios with two-digit year are generally 19xx era in this dataset.
                return 1900 + yy
        return None

    @staticmethod
    def _extract_birthplace(text):
        if not text:
            return ""
        patterns = [
            r"出生于([^，。；]+)",
            r"生于([^，。；]+)",
            r"([^，。；]+)人",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                value = m.group(1).strip()
                if len(value) <= 20:
                    return value
        return ""

    @staticmethod
    def _extract_nationality(text, fallback_country=""):
        if fallback_country:
            return fallback_country
        if not text:
            return ""
        if "中国" in text or "华语" in text or "台湾" in text or "台灣" in text:
            return "中国"
        return ""

    def parse_singer_detail(self, response):
        base = response.meta.get("base_item", {})
        item = SingerItem(base)

        brief = ""
        try:
            data = json.loads(response.text)
            brief = data.get("singerBrief", "") or ""
        except Exception:
            brief = ""

        birth_year = self._extract_birth_year(brief)
        if birth_year:
            item["singer_age"] = max(date.today().year - birth_year, 0)
        else:
            item["singer_age"] = ""

        item["singer_birthplace"] = self._extract_birthplace(brief)
        item["singer_nationality"] = self._extract_nationality(brief, item.get("singer_country", ""))

        if not item["singer_nationality"] and re.search(r"[\u4e00-\u9fff]", item.get("singer_name", "")):
            item["singer_nationality"] = "中国"
        if not item["singer_birthplace"]:
            item["singer_birthplace"] = "未知"

        yield item
        raise CloseSpider("singer_found")
