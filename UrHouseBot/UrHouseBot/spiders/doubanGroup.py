# -*- coding: utf-8 -*-
import scrapy

from UrHouseBot.UrHouseBot import parse_tool

class DoubangroupSpider(scrapy.Spider):
    key = '湖南路'
    name = "doubanGroup"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
    }
    # allowed_domains = ["https://www.douban.com/group/search?cat=1019&q=上海+租房"]
    # start_urls = ['http://https://www.douban.com/group/search?cat=1019&q=上海+租房/']

    def start_requests(self):
        urls = ['https://www.douban.com/group/search?cat=1019&q=上海+租房/']
        for url in urls:
            yield scrapy.Request(url, headers=self.headers)
    def parse(self, response):
        # 解析搜索小组出来的租房的小组
        print('-'*300)
        groups = response.css('.groups .result .title a')
        for group in groups:
            t = group.css('::text').extract_first()
            l = group.css('a::attr(href)').extract_first() + 'discussion?start=0'
            # gid = l.re(r'.*/(\d+)/.*')
            gid = group.css('a::attr(onclick)').re('.*sid: (\d+)}.*').pop()
            print('grpup id: ' + gid)
            print('link: ' + l)
            print('title: ' + t)

            target_search_link = 'https://www.douban.com/group/search?group=' + gid + '&cat='+ self.random_cat() +'&q=' + self.key + '&sort=time'
            yield scrapy.Request(l, headers=self.headers, callback=self.parse_group)

        # 下一页
        next = self.get_next_page_link(response)
        print('下一页: ' + next)
        # yield scrapy.Request(next, headers=self.headers)
        pass

    def parse_group(self, response):
        # 深度解析小组里的帖子
        print('解析小组页面' + '^'*100)

        pass

    def parse_search_result(self, response):
        # 解析根据设定的关键词的搜索结果的帖子
        print('接续搜索的关键词: ' + self.key)

        pass

    def parse_detail_article(self, response):
        # 解析具体的帖子
        print('解析具体梯子')

        pass
    