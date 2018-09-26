# -*- coding: utf-8 -*-
import scrapy
import UrHouseBot
from UrHouseBot import parse_tool
import re
from UrHouseBot.items import UrhousebotItem

class DoubangroupSpider(scrapy.Spider):
    keys = parse_tool.regions
    avoids = parse_tool.avoids
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
        # 解析小组列表页

        # print('-'*150)
        groups = response.css('.groups .result .title a')
        for group in groups:
            t = group.css('::text').extract_first().strip()
            l = group.css('a::attr(href)').extract_first().strip() + 'discussion?start=0'
            # gid = l.re(r'.*/(\d+)/.*')
            gid = group.css('a::attr(onclick)').re('.*sid: (\d+)}.*').pop()
            # print('grpup id: ' + gid)
            # print('link: ' + l)
            # print('title: ' + t)


            # 1. 返回在某小组里根据关键词搜索的结果(直接拼接id和关键词即使搜索结果的url)
            for key in self.keys:
                target_search_link = 'https://www.douban.com/group/search?group=' + gid \
                                     + '&cat=' + '1013' + '&q=' + key + '&sort=time'
                yield scrapy.Request(target_search_link, headers=self.headers, callback=self.parse_search_result)



            # 2. 返回解析某个小组的帖子的列表, 可以翻页
            yield scrapy.Request(l, headers=self.headers, callback=self.parse_group)

        # 3. 下一页
        next = parse_tool.get_next_page_link(response)
        # print('下一页: ' + next)
        yield scrapy.Request(next, headers=self.headers)
        pass



    def parse_group(self, response):
        # 解析某小组的帖子列表

        gtl = response.css('head title::text').extract_first().strip()
        # print('解析' + gtl + ' 页面' + '^'*100)

        # 获取下一页
        next = parse_tool.get_next_page_link(response)
        if next:
            # print(gtl + "小组的下一页" + next)
            yield scrapy.Request(next, headers=self.headers, callback=self.parse_group)

        titles = response.css('.olt .title')
        for t in titles:
            time = t.xpath('string(..//td[@class="time"][1])').extract_first().strip()
            if parse_tool.is_need_parse(time) is False:
                continue

            # 时间符合要求
            title = t.css('a::attr(title)').extract_first().strip()
            # print("时间合适-需要解析: " + title)
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
        ci = response.css('title::text').re(r'.*:(.+)$')
        if len(ci) > 0:
            print('搜索的关键词: ' + ci[0] + '\n')


        gtl = response.css('head title::text').extract_first().strip()
        # print('解析[' + gtl + '] 页面\n' + '^' * 100)

        # 获取下一页
        next = parse_tool.get_next_page_link(response)
        if next:
            # print(gtl + "小组的下一页" + next)
            yield scrapy.Request(next, headers=self.headers, callback=self.parse_search_result)

        titles = response.css('tbody .pl')
        for t in titles:
            time = t.css('.td-time::attr(title)').extract_first().strip()
            if parse_tool.is_need_parse(time) is False:
                continue

            # 时间符合要求
            title = t.css('.td-subject a::attr(title)').extract_first().strip()
            # print("时间合适-需要解析: " + title)
            link = t.css('.td-subject a::attr(href)').extract_first().strip()
            # 默认解析详情
            to_parse = self.parse_detail_article
            if parse_tool.filter_title(title):
                # title中含有关键字的话就直接解析目的文章
                to_parse = self.parse_target_article
            yield scrapy.Request(link, headers=self.headers, callback=to_parse)
        pass




    def parse_detail_article(self, response):
        # 解析具体的帖子, 查看是否含有需要解析的关键要素
        # print('解析具体帖子: \n' + response.url)

        # 获取正文内容
        content = response.css('#link-report').xpath('string(.//p)').extract_first().strip()
        response.meta['content'] = content

        # 判断是否符合第一需要
        key = parse_tool.filter_title(content)
        if key:
            response.meta['key'] = key
            self.parse_target_article(response)
            return
        else:
            return

        pass

    def parse_target_article(self, response):
        # 解析含有关键词的帖子

        print('解析具体帖子: \n' + response.url)
        # item = UrhousebotItem()

        # content = response.meta['content']
        # # 把含有附加条件的房源标为第一梯队
        # ur_need = parse_tool.filter_ur_need(content)
        # if  ur_need:
        #     item['level'] = 'first'

        completeTitle = response.css('.tablecc::text').extract_first()
        title = (completeTitle and completeTitle.strip()) or response.css('#content h1::text').extract_first().strip()
        # item['title'] = response.css('#content h1::text').extract_first().strip()
        # item['keys'] = response.meta['key']
        print('title: ' + title)
        # content = response.meta['content']
        # item['content'] = content
        # item['condition'] = ur_need

        # locations = re.findall(r'.{5,8}路', content)
        # payType = re.search(r'押.{1}付.{1}', content)

        # item['price'] = re.findall(r'\d{4}元{0,1}', content)
        # item['payType'] = payType
        # item['locations'] = locations

