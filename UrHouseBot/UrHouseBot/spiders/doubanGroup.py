# -*- coding: utf-8 -*-
import scrapy
import UrHouseBot
from UrHouseBot import parse_tool
import re
from UrHouseBot.items import UrhousebotItem
import datetime
import urllib
from PIL import Image
from scrapy import responsetypes
import random, string
import private
# import UrHouseBot.DouBanSelector as Selector

import json
import requests

# webhook_url = 'xxxxxxxxxxxxxxxxxx'
webhook_url = private.slackBotOpenInfoShare


def slackMe(content):
    slack_data = {
        'text': content,
        'type': 'mrkdwn',
    }
    response = requests.post(webhook_url,
                             data=json.dumps(slack_data),
                             headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ValueError(
            'Request to slack returned an error %s, the response is:\n%s' %
            (response.status_code, response.text))


class DoubangroupSpider(scrapy.Spider):
    # keys = parse_tool.regions
    # avoids = parse_tool.avoids
    name = "doubanGroup"
    start = True
    authors = []
    groups = {}
    titles = {}
    configs = {}
    blockLink = []
    monitors = {}
    headers = {
        'User-Agent':
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36',
    }

    custom_settings = {
        "RANDOM_DELAY": 10,
        "DOWNLOADER_MIDDLEWARES": {
            "UrHouseBot.middlewares.RandomDelayMiddleware": 999,
        }
    }

    def start_requests(self):
        self.configs['stop'] = False
        return [
            scrapy.Request('https://www.douban.com',
                           headers=self.headers,
                           callback=self.needLogin)
        ]

    def needLogin(self, response):
        self.log('看看要不要登录')
        if len(re.findall('登录',
                          response.xpath('string(.)').get().strip())) > 0:
            self.log(' 需要登录')
            yield scrapy.FormRequest(
                "https://accounts.douban.com/passport/login",
                headers=self.headers,
                meta={"cookiejar": 1},
                callback=self.parse_before_login)
        else:
            self.log('不需要登录')
            yield self.startCrawl()

    def parse_before_login(self, response):
        '''
        登录表单填充，查看验证码
        '''
        self.log("登录前表单填充")
        captcha_id = response.xpath(
            '//input[@name="captcha-id"]/@value').extract_first()
        captcha_image_url = response.xpath(
            '//img[@id="captcha_image"]/@src').extract_first()
        if captcha_image_url is None:
            self.log("登录时无验证码")
            formdata = {
                'ck': '',
                'name': private.doubanAccount, #'!!warning__这里 填上你豆瓣的 ID__!!!',
                'password': private.doubanPwd,   #'!!warning__这里填上豆瓣密码__!!',
                'remember': 'false',
                'ticket': ''
            }
        else:
            self.log("登录时有验证码")
            save_image_path = "./captcha.jpeg"
            #将图片验证码下载到本地
            urllib.urlretrieve(captcha_image_url, save_image_path)
            #打开图片，以便我们识别图中验证码
            open()
            try:
                im = Image.open('captcha.jpeg')
                im.show()
            except:
                pass
            #手动输入验证码
            captcha_solution = input('根据打开的图片输入验证码:')
            formdata = {
                'ck': '',
                'name': '466781718@qq.com',
                'password': '987412ds',
                'remember': 'false',
                'ticket': ''
            }

        self.log("登录中")
        #提交表单
        return scrapy.FormRequest(
            'https://accounts.douban.com/j/mobile/login/basic',
            headers=self.headers,
            formdata=formdata,
            callback=self.parse_after_login)

    def parse_after_login(self, response):
        '''
        验证登录是否成功
        '''
        info = json.loads(response.body)
        self.log(f'登录结果: {info}')
        if response.status != 200:
            self.log('登录失败')
            return

        if info["status"] == "failed":
            self.log(f"登录失败, {info['需要图形验证码']}")
        self.log(
            f'登录成功'
        )
        toCrawl = self.startCrawl()
        for request in toCrawl:
            yield request

    def startCrawl(self):
        self.log('开始抓取')
        slackMe(datetime.datetime.today().strftime('%Y-%m-%d %H:%M') +
                "=" * 500 +
                datetime.datetime.today().strftime('%Y-%m-%d %H:%M'))
        self.loadCrawled()
        url = 'https://www.douban.com/group/search?cat=1019&q=上海+租房'
        needCrawl = []
        for title, dic in self.titles.items():
            if isinstance(dic, str):
                continue
            if dic.get("hadReq") and not dic.get("hadResp"):
                link = dic.get("link")
                oTitle = dic.get("title")
                if self.isBlock(link, oTitle):
                    continue
                req = scrapy.Request(link, headers=self.headers, callback=self.parse_detail_article)
                req.meta["tag_info"] = f'上次未完成: 帖子: -> {oTitle}:{dic.get("link")}'
                req.meta["title"] = oTitle
                needCrawl.append(req)
        return [scrapy.Request(url, headers=self.headers, callback=self.parse)]+needCrawl

    def close(self, reason):
        msg = "结束" + reason
        time = datetime.datetime.today().strftime('%Y-%m-%d %H:%M')
        if reason == "finish" and "gidPage" in self.configs:
            del self.configs["gidPage"]
            msg = "完成一轮" + time + "*" * 50

        self.saveCrawled()
        slackMe(msg)
        self.log('完成一轮')

    def parseIfNeed(self, response):
        # 组的帖子太少, 或者日期太旧, 都不进行爬取

        #  小组 id
        gid = response.meta.get('gid')
        t = response.meta.get('title')
        l = response.meta.get('link')

        dates = response.xpath('//td[@class="time"]/text()').getall()
        if not (dates and len(dates) == 25 and parse_tool.is_need_parse(dates[24])):
            # 将这个组标记为不爬取
            self.blockLink.append(l)
            self.groups[gid]['dead'] = True
            self.log(f'🚯🚯该小组已长期不活跃, 加进 dead 和 block: {t}, 首页帖子: {len(dates)} 个, url: {response.url}')
            self.saveCrawled()
            return

        firstPageLink = l + 'discussion?start=0'
        if self.isBlock(firstPageLink, f'小组: {t}') or self.isBlock(gid, f'小组: {gid} _ {t}'):
            self.log(f'[是否爬取->该小组 {t} _ {gid} 链接已被屏蔽: {firstPageLink}]')
            return

        # 1. 返回在某小组里根据关键词搜索的结果(直接拼接id和关键词即使搜索结果的url)
        for key in parse_tool.getRegions():
            target_search_link = 'https://www.douban.com/group/search?group=' + gid \
                                  + '&cat=' + '1013' + '&q=' + key + '&sort=time'
            if self.isBlock(target_search_link):
                continue
            # 保存搜索的链接
            monitorKey = f'{gid}_{key}'
            if monitorKey not in self.monitors:
                self.log(f'👀👀👀👀👀标记监控{monitorKey}, 小组: {t}, 关键字: {key}')
                self.monitors[monitorKey] = {
                    "for": f'goup:{t} -> {key}',
                    "link": target_search_link,
                    "monitor": False
                }
            if self.isBlock(monitorKey, target_search_link):
                continue
            request = scrapy.Request(target_search_link,
                                  headers=self.headers,
                                  callback=self.parse_search_result)
            request.meta["monitorKey"] = monitorKey
            request.meta['tag_info'] = f'组: {t}, 关键字搜索: {key}'
            yield request

        #  保存某个组的首页
        monitorKey = f'{gid}'
        if monitorKey not in self.monitors:
            self.log(f'👀👀👀👀👀标记监控{monitorKey}')
            self.monitors[monitorKey] = {
              "for": f'all group post: {t}',
              "link": firstPageLink,
              "monitor": False
            }
        # 2. 返回解析某个小组的帖子的列表, 可以翻页
        if self.isBlock(l, "判断是否需要爬取"):
            return
        gRequest = scrapy.Request(firstPageLink,
                              headers=self.headers,
                              callback=self.parse_group)
        gRequest.meta['monitorKey'] = monitorKey
        gRequest.meta['tag_info'] = f'小组内爬取, 组{t}'
        yield gRequest

    def randomString(self, prefix='&', k=6):
        return f'{prefix}nonce={"".join(random.choices(string.ascii_letters + string.digits, k=k))}'

    def parse(self, response):
        # 解析小组列表页
        # 先进小组, 看看需不需要进一步搜索或者翻页
        forceParse = response.meta.get('forceParse', False)
        if 'stop' in self.configs and self.configs['stop'] and not forceParse:  # 组已经走过一次, 不需要在翻页获取
            self.log(
                f'🚫🚫🚫🚫🚫已经成功获取晚所有搜索出的小组, 共{len(self.groups.keys())}个小组🚫🚫🚫🚫🚫🚫🚫🚫🚫'
            )
            for gid, dic in self.groups.items():
                link = dic.get('link')
                if link and self.isBlock(link, '解析小组列表'):
                    continue
                if dic.get('dead', False):
                    self.log(f'🚯🚯🚯🚯🚯🚯该链接已 dead: {link}')
                    continue
                request = scrapy.Request(link + 'discussion?start=50'+self.randomString(), headers=self.headers, callback=self.parseIfNeed)
                request.meta['title'] = dic.get('title')
                request.meta['link'] = link
                request.meta['gid'] = gid
                yield request
            return

        groups = response.xpath('//div[@class="content"]')
        groupNum = len(groups)
        for idx, group in enumerate(groups):
            # 小组标题
            # t = group.css('::text').extract_first().strip()
            t = group.xpath('.//div[@class="title"]/h3/a/text()').get().strip()
            if len(re.findall(r'同志|拉拉', t)) > 0:
                continue
            # 小组链接
            l = group.css('a::attr(href)').extract_first().strip()
            if self.isBlock(l):
                continue

            gid = group.css('a::attr(onclick)').re('.*sid: (\d+)}.*').pop()
            if gid in self.monitors and self.monitors[gid]['monitor']:
                continue
            if gid in self.groups and self.groups[gid].get('dead', False):
                continue
            # 成员数
            # string(//div[@class="info"])
            request = scrapy.Request(l + 'discussion?start=50'+self.randomString(),
                                     headers=self.headers,
                                     callback=self.parseIfNeed)

            request.meta['title'] = t
            request.meta['link'] = l
            request.meta['gid'] = gid
            self.groups[gid] = dict(title=t, link=l, dead=False)
            yield request

        # 3. 下一页
        next = ''
        if 'gidPage' in self.configs and self.start:
            next = self.configs['gidPage']
        else:
            next = parse_tool.get_next_page_link(response)

        self.start = False
        if next and 'http' in next:
            # start = re.findall(r'start=(\d+)&', next)
            self.log(f'搜组结果_下一页: {next}')
            self.configs["gidPage"] = next
            if self.isBlock(next):
                return
            req = scrapy.Request(next,
                                 headers=self.headers,
                                 callback=self.parse)
            req.meta['forceParse'] = True
            yield req
        else:
            self.log(f"!!!!!搜索组_已经拿不到下一页")
            if "gidPage" in self.configs:
                del self.configs["gidPage"]
            self.configs["stop"] = True

    def routineMonitor():
        # todo:  某个小组的帖子搜完之后, 就回到第一页开始监控.
        # 记录每个小组的第一页, 每个小组搜索的第一页,
        pass

    def parse_group(self, response):
        # 解析某小组的帖子列表, 用来全组便利符合title条件的帖子

        tag_info = response.meta.get("tag_info", "")
        monitorKey = response.meta.get("monitorKey")
        needMonitor = self.monitors[monitorKey]['monitor']
        page = response.meta.get('page', 1)

        # 小组标题
        gtl = response.css('head title::text').extract_first().strip()
        need_more = True
        # 帖子标题
        titles = response.css('.olt .title')
        totalTitleNum = len(titles)
        if (totalTitleNum == 0) or (page == 1 and totalTitleNum < 24):
            self.log(
                f'爬取小组内容, 第 {page} 页title数: {totalTitleNum}, 加入 block🚫🚫🚫🚫🚫🚫')
            self.blockLink.append(response.url)
            self.monitors[monitorKey]['monitor'] = False
            return

        self.log(f' 🌞🌞🌞🌞🌞🌞🌞 爬取 {gtl} 小组 第 {page} 页内容, {totalTitleNum} 条帖子')
        for idx, t in enumerate(titles):
            # 获取时间
            title = t.css('a::attr(title)').extract_first().strip()
            link = t.css('a::attr(href)').extract_first()
            time = t.xpath(
                'string(..//td[@class="time"][1])').extract_first().strip()
            if not parse_tool.is_need_parse(time, 1 if needMonitor else 18):
                # 时间不符合的跳过
                need_more = False
                if page == 1 and idx < 10:
                    self.log(f'页面符合要求的很少: 直接跳过: 组: {gtl}, page: {page}, index: {idx} 标题: {t}, link: {link}')
                    return
                self.log(f'🕘🕘🕘🕘🕘🕘小组:{gtl}_时间过期: {time}, 标题: {title}, 链接: {link}')
                break
            # 时间符合要求
            #  楼主被屏蔽的跳过
            author = t.xpath(
                'string(following-sibling::td[1])').extract_first().strip()
            if author in self.authors: # 仅仅判断在不在, 在的话就不继续请求解析这个帖子了
                continue
            #  帖子 title 重复的跳过
            if self.isCrawledTitle(title, link):
                continue
            # 默认解析详情
            to_parse = self.parse_detail_article
            (isTarget, keys) = parse_tool.filter_title(title.strip() + author,
                                                       f'解析小组: {title}', link)
            if isTarget:
                # title中含有关键字的话就直接解析目的文章
                to_parse = self.parse_target_article
            elif keys:
                continue
            if self.isBlock(link, "解析小组帖子列表"):
                continue
            request = scrapy.Request(link, headers=self.headers, callback=to_parse)
            request.meta["tag_info"] = f'tagInfo: {tag_info}, 帖子: {idx}/{totalTitleNum} -> {title}'
            request.meta["title"] = title
            self.markReqTitle(title, link)
            yield request

        # 获取下一页
        # self.showCurrentInfo()
        next = parse_tool.get_next_page_link(response)
        if next and need_more and not needMonitor:
            if self.isBlock(next, f'小组:{gtl}'):
                return
            req = scrapy.Request(next,
                                 headers=self.headers,
                                 callback=self.parse_group)
            req.meta['monitorKey'] = monitorKey
            req.meta['tag_info'] = tag_info
            req.meta['page'] = page + 1
            yield req
        else:
            self.log(f'小组页_拿不到下一页或不需要更多: {next} / needMore: {need_more}, 是否监控: {needMonitor}')
            self.monitors[monitorKey]['monitor'] = True

            link = self.monitors[monitorKey]['link']
            if self.isBlock(link, f'小组:{gtl}'):
                return
            monitorLink = link+self.randomString('?')
            req = scrapy.Request(monitorLink, headers=self.headers, callback=self.parse_group)
            req.meta['monitorKey'] = monitorKey
            req.meta['tag_info'] = tag_info + "监控中👁👁👁"
            self.log(f"👁👁👁👁👁👁👁👁{monitorKey}  __正在监控: {monitorLink}")
            # yield req


    def showCurrentInfo(self):
        return
        monitors = self.monitors
        self.log(f'''
        🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖

        当前监控: {len(list(filter(lambda g: g["monitor"] and g["monitor"] == True, self.monitors)))} 个
        有效小组: {len(list(filter(lambda g: g["dead"] and g["dead"] == False, self.groups)))} 个
        屏蔽数量: {len(self.blockLink)}

        🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖
        ''')

    def parse_search_result(self, response):
        # 解析根据设定的关键词的搜索某小组的结果的帖子
        tag_info = response.meta.get('tag_info', '')
        monitorKey = response.meta.get("monitorKey")
        needMonitor = self.monitors[monitorKey]['monitor']
        page = response.meta.get('page', 1)

        ci = response.css('title::text').re(r'.*:(.+)$')
        # if len(ci) > 0:
        #     self.log('搜索的关键词: ' + ci[0] + '\n')

        gtl = response.css('head title::text').extract_first().strip()
        location = response.xpath('string(//h1/div)').get().strip()
        need_more = True
        titles = response.css('tbody .pl')
        self.log(f' 🔦🔦🔦🔦🔦🔦🔦🔦🔦🔦🔦🔦🔦 组位置: {tag_info} 页面->{len(titles)}条title\n 是否正在监控: {needMonitor}' + '^' * 100)
        totalTitleNum = len(titles)
        if (totalTitleNum == 0) or (page == 1 and totalTitleNum < 47):
            # 加入黑名单, 这个以后就直接过滤掉
            self.log(
                f'爬取搜索结果, 第 {page} 页title数: {totalTitleNum}, 加入 block🚫🚫🚫🚫🚫🚫')
            self.blockLink.append(response.url)
            self.blockLink.append(monitorKey)
            self.monitors[monitorKey]['monitor'] = False
            return

        # self.showCurrentInfo()
        for idx, t in enumerate(titles):
            title = t.css('.td-subject a::attr(title)').extract_first().strip()
            link = t.css('.td-subject a::attr(href)').extract_first().strip()
            time = t.css('.td-time::attr(title)').extract_first().strip()
            if not parse_tool.is_need_parse(time, 1 if needMonitor else 18):
                need_more = False
                break
            if self.isCrawledTitle(title, link):
                continue
            if self.isBlock(link):
                continue

            # 默认解析详情
            to_parse = self.parse_detail_article
            (isTarget, keys) = parse_tool.filter_title(title,
                                                       f' 解析搜索关键词: {title}',
                                                       link)
            if isTarget:
                # title中含有关键字的话就直接解析目的文章
                to_parse = self.parse_target_article
            elif len(keys) > 0:
                continue

            self.log(f'可以解析帖子-> 时间: {time} 标题: {title}, link: {link}')
            request = scrapy.Request(link,
                                     headers=self.headers,
                                     callback=to_parse)
            request.meta["tag_info"] = f'tagInfo: {tag_info}, 帖子: {idx}/{totalTitleNum} -> {title}'
            request.meta["title"] = title
            request.meta["monitorKey"] = monitorKey
            self.markReqTitle(title, link)
            yield request

        # 获取下一页
        next = parse_tool.get_next_page_link(response)
        if next and need_more and not needMonitor:
            if self.isBlock(next):
                return
            req = scrapy.Request(next,
                                 headers=self.headers,
                                 callback=self.parse_search_result)
            req.meta['tag_info'] = tag_info
            req.meta["monitorKey"] = monitorKey
            req.meta['page'] = page + 1
            self.log(f'搜索关键字翻页到: {page+1},  link: {next}')
            yield req
        else:
            self.log(f'小组查询关键字_拿不到下一页或不需要更多: {next} / needMore: {need_more},  是否监控: {needMonitor}')
            self.monitors[monitorKey]['monitor'] = True
            link = self.monitors[monitorKey]['link']
            if self.isBlock(link):
                return
            monitorLink = link + self.randomString()
            req = scrapy.Request(monitorLink,
                                  headers=self.headers,
                                  callback=self.parse_search_result)
            self.log(f"👁👁👁👁👁👁{monitorKey}  __正在监控: {monitorLink}")
            req.meta["monitorKey"] = monitorKey
            req.meta['tag_info'] = f'{tag_info}_监控中👁👁👁👁👁' if '监控' not in tag_info else tag_info
            # yield req

    def parse_detail_article(self, response):
        # 解析具体的帖子, 查看是否含有需要解析的关键要素
        reqTitle = response.meta.get("title")
        if reqTitle:
            self.markRespOfTitle(reqTitle, response.url)

        # 获取楼主
        author = response.css('.from a::text').extract_first().strip()

        completeTitle = response.css('.tablecc::text').extract_first()
        title = (completeTitle and completeTitle.strip()) or response.css(
            '#content h1::text').extract_first().strip()

        # 获取正文内容
        content = response.xpath(
            'string(//div[@class="topic-richtext"])').extract_first().strip()

        # 判断是否符合第一需要
        (isTarget, keys) = parse_tool.filter_title(content + author, title=f'解析具体: {title}',
                                                   link=response.url, use='content')
        if isTarget:
            response.meta['key'] = keys
            # response.meta['content'] = content
            # response.meta['author'] = author
            self.parse_target_article(response)
            tagInfo = response.meta.get("tag_info", 'no_tag_info')
            self.log(f'\n\n解析具体帖子: \n{tagInfo} < {response.url} >\n\n{"🉑"*100}\n\n')
            return
        else:
            self.log(f'解析具体帖子,  命中: {isTarget}, 关键词: {keys}')
            return

    def parse_target_article(self, response):
        # 解析含有关键词的帖子
        reqTitle = response.meta.get("title")
        if reqTitle:
            self.markRespOfTitle(reqTitle, response.url)

        tagInfo = response.meta.get("tag_info", 'no_tag_info')
        self.log(f'❗️❗️❗️❗️❗️❗️❗️❗️❗️❗️ \n解析目标帖子: {tagInfo} -> {response.url}')
        # 获取楼主
        allContent = response.xpath(
            'string(//div[@class="article"])').get().strip()
        if len(re.findall(r'已[出租]', allContent)) > 0:
            self.log('\n 已租.........💢.💢.💢.💢.💢.💢')
            return
        time = response.xpath(
            'string(//span[@class="from"]/following-sibling::span)').get(
            ).strip()
        if not parse_tool.is_need_parse(time):
            self.log(f'\n时间过期: {time}')
            return
        author = response.css('.from a::text').extract_first().strip()
        if self.isCrawledAuthor(author):
            self.log(f'该楼主已经发过贴: {author}......❓.❓.❓.❓')
            return
        content = response.xpath('//div[@class="topic-richtext"]').get().strip()
        # 转换图片
        content = re.sub(r'<img src="(.*?)" .*?>', r' \nImage: \1  ', content, 4)
        content = scrapy.Selector(
            text=content).xpath(r'string(.)').get().strip()

        # 转换电话
        content = re.sub(r'(1[3578]\d{9})', r' <tel:\1|\1> ', content)

        # 标机可能的价格
        content = re.sub(r'([^\d/p])(\d{4})([\D]{1})', r'\1 `\2` \3', content)

        # 去多余的空格
        content = re.sub(r' {2,}', ' ', content)

        completeTitle = response.css('.tablecc::text').extract_first()
        title = (completeTitle and completeTitle.strip()) or response.css(
            '#content h1::text').extract_first().strip()
        replies = self.getReply(response, author)
        reply = '\n- '.join(replies)
        if len(re.findall(r'豆友\d{6,9}', reply)) > 10:
            self.log(f'可能是机器人刷帖: "豆友 xxxx 回复数量: {len(replies)} 条')
            return
        (hit, keys) = parse_tool.filter_title(content + reply + f'解析目标{title}' + author,
                                              title, response.url, use='content')

        def strip(s):
            return s.strip()

        if hit:
            # 先高亮下`女`关键词, 有些漏掉的, 起码在看的时候容易看出来
            content = re.sub(r'(女)', r' `\1` ', content)
            seperator = '>' * 15
            date = datetime.datetime.today().strftime('%Y-%m-%d %H:%M')
            content = re.sub(f'({parse_tool.appendKeys(parse_tool.getRegions())})',
                   r' `\1` ', content)
            fromRequest = tagInfo.split('->')[0]
            slackMe(' \n '.join([
                f'```{seperator}{date} \n楼主: {author}\nfrom: {fromRequest} \n关键词: `{list(map(strip, keys))}` ```',
                f' ` <{response.url}|{title}> `  \n{time}', content,
                reply
            ]))
            self.log(f'\n{"✅"*10}\n发送: {title} \n链接: {response.url}\n')

        # 将去重数据保存到本地
        self.saveCrawled()

    def getReply(self, response, author):
        allReply = response.xpath('//div[@class="reply-doc content"]')
        replyContents = {}
        for idx, reply in enumerate(allReply):
            au = reply.xpath('string(./div[1]//a)').get().strip().replace(
                ' ', '')
            t = reply.xpath('string(./div[1]//span)').get().strip()
            c = reply.xpath(
                'string(./p[@class=" reply-content"])').get().strip().replace(
                    ' ', '')
            c = re.sub(r'(1[3578]\d{9})', r' <tel:\1|\1> ', c)
            c = re.sub(r'([^\d/p])(\d{4})([\D]{1})', r'\1 `\2` \3', c)
            showAu = '楼主' if author == au else au

            replyContents[c] = dict(au=showAu, time=t, index=idx)
            # self.log(f'[ {c} ]: {t} > {showAu}')
        ans = []
        for key, value in replyContents.items():
            ans.append(
                f'{value.get("index")}. [ {key} ]: {value.get("time")} > {value.get("au")}'
            )
        return ans

    def isBlock(self, link, info=None, url=None):
        if link in self.blockLink:
            #  一般不会再有什么帖子在那里发了, 直接回拒
            self.log(
                f'🚯🚯死链或者是上次没有内容的结果, 链接: {link}, \n额外信息: {info}, link: {url}'
            )
            return True
        else:
            return False

    # 是否抓去过标题
    def dealTitle(self, title):
        title = re.sub(' ', '', title)
        return title.strip().lower()[:30]

    def isCrawledTitle(self, title, link):
        oTitle = title
        title = self.dealTitle(title)
        if title in self.titles:
            self.log(f"title 去重: {title}")
            return True
        else:
            # 标记在请求, 未响应.
            self.log(f'标记 title 爬取: {title}, link: {link}')
            self.titles[title] = dict(link=link, title=oTitle, hadResp=False, hadReq=False)
            return False

    #  标机已爬取有返回, (区别判断, 以免请求在排队时候中断了之后, 在启动时)
    def markRespOfTitle(self, title, link):
        oTitle = title
        title = self.dealTitle(title)
        self.titles[title] = dict(link=link, title=oTitle, hadReq=True, hadResp=True)

    # 标机已请求, 未返回
    def markReqTitle(self, title, link):
        oTitle = title
        title = self.dealTitle(title)
        self.titles[title] = dict(link=link, title=oTitle, hadReq=True, hadResp=False)

    # 是否抓去过作者
    def isCrawledAuthor(self, author):
        if author in self.authors:
            return True
        else:
            self.authors.append(author)
            return False

    # 保存抓取数据
    def saveCrawled(self):
        with open('./titles.json', 'w') as f:
            json.dump(self.titles, f)

        with open('./authors.json', 'w') as f:
            json.dump(self.authors, f)

        with open('./groups.json', 'w') as f:
            json.dump(self.groups, f)

        with open('./configs.json', 'w') as f:
            self.configs["block_link"] = self.blockLink
            self.configs["monitors"] = self.monitors
            json.dump(self.configs, f)

    # 加载数据
    def loadCrawled(self):
        try:
            with open('./titles.json', 'r') as f:
                try:
                    self.log('加载 titles.json')
                    data = json.load(f)
                    self.titles = data
                    self.log(f'加载{len(self.titles.keys())}条标题')
                except Exception as error:
                    self.log(f'title文件错误{error}')
                    # self.titles = {}
                    raise
                # else:
                # self.titles = data
        except:
            self.log('没有title文件')
            self.titles = {}
        try:
            with open('./authors.json', 'r') as f:
                try:
                    self.log('加载 authors.json')
                    data = json.load(f)
                    self.log(f'加载楼主: {len(data)}')
                    self.authors = data
                except:
                    self.log('文件authors.json加载出错')
                    raise
                # else:
                #     self.authors = data
        except:
            self.log('没有authors文件')
            self.authors = []
        try:
            with open('./groups.json', 'r') as f:
                try:
                    self.log('加载 groups.json')
                    data = json.load(f)
                    self.log(f'小组数: {len(data)}')
                    self.groups = data
                except:
                    self.log('文件groups.json 加载出错')
                    # self.groups = {}
                    raise
                # else:
                #     self.groups = data
        except:
            self.log('没有groups文件')
            self.groups = {}
        try:
            with open('./configs.json', 'r') as f:
                try:
                    self.log(' 加载 configs 文件')
                    data = json.load(f)
                    block_link = data.get("block_link")
                    monitors = data.get("monitors")
                    self.configs = data
                    if 'stop' not in data:
                        self.configs['stop'] = False
                    if 'block_link' not in data:
                        self.configs['block_link'] = []
                    if 'monitors' not in data:
                        self.configs['monitors'] = {}
                    self.blockLink = block_link if block_link else []
                    self.monitors = monitors if monitors else {}
                except:
                    self.log('文件configs.json')
                    # self.configs = {}
                    raise
                # else:
                #     self.configs = data
                #     self.blockLink = blockLink if blockLink else []
                #     self.monitors = monitors if monitors else {}
        except:
            self.log('没有configs文件')
            self.configs = {}
