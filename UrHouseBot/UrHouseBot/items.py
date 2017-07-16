# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class UrhousebotItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()

    title = scrapy.Field()
    keys = scrapy.Field()
    conditions = scrapy.Field()

    locations = scrapy.Field()
    price = scrapy.Field()
    content = scrapy.Field()

    images = scrapy.Field()

    level = scrapy.Field()
    payTpe = scrapy.Field()