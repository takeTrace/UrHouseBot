# -*- coding: utf-8 -*-
import scrapy


class DoubangroupSpider(scrapy.Spider):
    name = "doubanGroup"
    allowed_domains = ["https://www.douban.com/group/search?cat=1019&q=上海+租房"]
    start_urls = ['http://https://www.douban.com/group/search?cat=1019&q=上海+租房/']

    def parse(self, response):
        pass
