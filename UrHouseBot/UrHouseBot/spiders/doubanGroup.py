# -*- coding: utf-8 -*-
import scrapy
import UrHouseBot
from UrHouseBot import parse_tool

class DoubangroupSpider(scrapy.Spider):
    keys = parse_tool.keyword
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
        print('-'*150)
        groups = response.css('.groups .result .title a')
        for group in groups:
            t = group.css('::text').extract_first().strip()
            l = group.css('a::attr(href)').extract_first().strip() + 'discussion?start=0'
            # gid = l.re(r'.*/(\d+)/.*')
            gid = group.css('a::attr(onclick)').re('.*sid: (\d+)}.*').pop()
            print('grpup id: ' + gid)
            print('link: ' + l)
            print('title: ' + t)


            # 1. 返回在某小组里根据关键词搜索的结果(直接拼接id和关键词即使搜索结果的url)
            for key in self.keys:
                target_search_link = 'https://www.douban.com/group/search?group=' + gid \
                                     + '&cat=' + '1013' + '&q=' + key + '&sort=time'
                yield scrapy.Request(target_search_link, headers=self.headers, callback=self.parse_search_result)



            # 2. 返回解析某个小组的帖子的列表, 可以翻页
            yield scrapy.Request(l, headers=self.headers, callback=self.parse_group)

        # 3. 下一页
        next = parse_tool.get_next_page_link(response)
        print('下一页: ' + next)
        yield scrapy.Request(next, headers=self.headers)
        pass



    def parse_group(self, response):
        # 深度解析小组里的帖子
        gtl = response.css('head title::text').extract_first().strip()
        print('解析' + gtl + ' 页面' + '^'*100)

        # 获取下一页
        next = parse_tool.get_next_page_link(response)
        if next:
            print(gtl + "小组的下一页" + next)
            yield scrapy.Request(next, headers=self.headers, callback=self.parse_group)

        titles = response.css('.olt .title')
        for t in titles:
            time = t.xpath('string(..//td[@class="time"][1])').extract_first().strip()
            if parse_tool.is_need_parse(time) is False:
                continue

            # 时间符合要求
            title = t.css('a::attr(title)').extract_first().strip()
            print("时间合适-需要解析: " + title)
            link = t.css('a::attr(href)').extract_first()
            # 默认解析详情
            to_parse = self.parse_detail_article
            if parse_tool.filter_title(title):
                # title中含有关键字的话就直接解析目的文章
                to_parse = self.parse_target_article
            yield scrapy.Request(link, headers=self.headers, callback=to_parse)

        pass




    def parse_search_result(self, response):
        # 解析根据设定的关键词的搜索某小组的结果的帖子
        print('接续搜索的关键词: ' + response.css('title::text')).re('.*:(.+)$').extract_first().strip()

        pass




    def parse_detail_article(self, response):
        # 解析具体的帖子, 查看是否含有需要解析的关键要素
        print('解析具体帖子' + response.url)

        pass

    def parse_target_article(self, response):
        # 解析含有关键词的帖子,
        print('帖子中包含有相关的关键词, 且未出现已出租的字样, 再次深度解析' + response.url)
