# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class QqmusicspiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class MusicItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    singer_id = scrapy.Field()
    singer_mid = scrapy.Field()
    singer_name = scrapy.Field()
    subtitle = scrapy.Field()
    song_id = scrapy.Field()
    song_mid = scrapy.Field()
    song_name = scrapy.Field()
    song_time_public = scrapy.Field()
    lyric = scrapy.Field()
    album_name = scrapy.Field()
    language = scrapy.Field()
    song_type = scrapy.Field()
    hot_comments = scrapy.Field()
    song_url = scrapy.Field()
    # company = scrapy.Field()


class SingerItem(scrapy.Item):
    singer_id = scrapy.Field()
    singer_mid = scrapy.Field()
    singer_name = scrapy.Field()
    singer_pic = scrapy.Field()
    singer_country = scrapy.Field()
    singer_genre = scrapy.Field()
    singer_index = scrapy.Field()
    singer_nationality = scrapy.Field()
    singer_birthplace = scrapy.Field()
    singer_age = scrapy.Field()