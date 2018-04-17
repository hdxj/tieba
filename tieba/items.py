# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class TiebaItem(scrapy.Item):
    # define the fields for your item here like:
    user = scrapy.Field()
    content = scrapy.Field()
    dateline = scrapy.Field()
    url = scrapy.Field()
    rep_num = scrapy.Field()
