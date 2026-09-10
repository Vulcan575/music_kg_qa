# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from QQMusicSpider.items import MusicItem
import json
from scrapy.exceptions import DropItem


class DuplicatesPipeline(object):
    """
    根据音乐的song_id，对爬取过的音乐进行去重
    """

    def __init__(self):
        self.song_ids = set()

    def process_item(self, item, spider):
        if isinstance(item, MusicItem):
            if item['song_id'] in self.song_ids:
                raise DropItem("Duplicate item found: %s" % item)
            else:
                self.song_ids.add(item['song_id'])
                return item


class QqmusicspiderPipeline(object):
    def __init__(self):
        self.music_path = "music"
        self.song_ids = set()

        # 读取已存在的 music 文件中的 song_id，避免重复写入
        try:
            with open(self.music_path, "r", encoding="utf8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        song_id = data.get('song_id')
                        if song_id:
                            self.song_ids.add(song_id)
                    except Exception:
                        continue
        except FileNotFoundError:
            pass

        # 追加写入模式，每次新数据写到文件末尾
        self.file = open(self.music_path, "a", encoding="utf8")

    def process_item(self, item, spider):
        if isinstance(item, MusicItem):
            song_id = item.get('song_id')
            if song_id in self.song_ids:
                raise DropItem("Duplicate item found (already in music file): %s" % item)
            self.song_ids.add(song_id)
            line = json.dumps(dict(item), ensure_ascii=False) + "\n"
            self.file.write(line)
        return item

    def close_spider(self, spider):
        self.file.close()


