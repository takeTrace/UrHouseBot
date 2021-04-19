# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals, Request
import requests

from UrHouseBot.spiders import doubanGroup

aws = "http://13.125.214.188"


class UrhousebotSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


# -*- coding:utf-8 -*-

import logging
import random
import time


class RandomDelayMiddleware(object):
    def __init__(self, delay):
        self.delay = delay

    @classmethod
    def from_crawler(cls, crawler):
        delay = crawler.spider.settings.get("RANDOM_DELAY", 2)
        if not isinstance(delay, int):
            raise ValueError("RANDOM_DELAY need a int")
        return cls(delay)

    def process_request(self, request, spider):
        # print("don't delay cause there is proxy change")
        delay = random.randint(0, self.delay)
        logging.debug("### random delay: %s s ###" % delay)
        time.sleep(delay)


from fake_useragent import UserAgent


class RandomUserAgentMiddlware(object):
    # 随机更换user-agent
    def __init__(self, crawler):
        super(RandomUserAgentMiddlware, self).__init__()
        self.ua = UserAgent()
        self.ua_type = crawler.settings.get("RANDOM_UA_TYPE", "random")

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        def get_ua():
            return getattr(self.ua, self.ua_type)

        ua = get_ua()
        logging.debug(f"USerAgen: {ua}")
        request.headers.setdefault('User-Agent', ua)


def getSmartProxy():
    res = requests.get(f'{aws}:35050/api/v1/proxy/?region=中国')
    if res.status_code == 200:
        p = res.json()['data']['proxy']
        return f'http://{p}'
    else:
        print(f'XXXXXXXXXXXXXXXXXXXXXXX没有拿到代理: {res.content}')
        return None


def proxyFromproxy_pool():
    res = requests.get(f'{aws}:5010/get')
    if res.status_code == 200:
        p = res.json()['data']['proxy']
        return f'http://{p}'
    else:
        logging.debug(f'XXXXXXXXXXXXXXXXXXXXXXX没有拿到代理: {res.content}')
        return None


def proxyFromProxyPool():
    res = requests.get(f'{aws}:5555/random')
    if res.status_code == 200:
        p = f'http://{res.text.strip()}'
        return p
    else:
        logging.debug(f'XXXXXXXXXXXXXXXXXXXXXXX没有拿到代理')
        return None


class ProxyMiddleware(object):
    count = 51
    proxy = "null"

    def process_request(self, request, spider):
        self.useProxyPoolRepo(request)
        # self.useSmartProxyPoolRepo(request)
        # self.useWebSpider(request)

    def useProxyPoolRepo(self, request):
        proxy = proxyFromProxyPool()
        fail_times = 1
        while proxy and doubanGroup.redirectCount.get(proxy, 0) > 10:
            # time.sleep(fail_times)
            fail_times = fail_times + 1
            logging.debug(
                f'代理 {proxy} block 过多, {doubanGroup.redirectCount.get(proxy, 0)}, 重新获取 {fail_times} 次'
            )
            proxy = proxyFromProxyPool()
        logging.debug(f'成功: {proxy}')
        request.meta["proxy"] = proxy
        logging.debug(f'获取代理: {proxy} -> {request.url}')

    def useWebSpider(self, request):
        p = proxyFromproxy_pool()
        times = 1
        while p or doubanGroup.redirectCount.get(p, 0) > 10:
            time.sleep(times)
            times = times + 1
            logging.debug(
                f'代理 {p} block 过多, {doubanGroup.redirectCount.get(p, 0)}, 重新获取 {times} 次'
            )
            p = proxyFromproxy_pool()
        logging.debug(f'成功: {p}')
        request.meta["proxy"] = p
        logging.debug(f'获取代理: {p} -> {request.url}')

    def useSmartProxyPoolRepo(self, request):
        p = getSmartProxy()
        times = 1
        while p and doubanGroup.redirectCount.get(p, 0) > 10:
            time.sleep(times)
            times = times + 1
            logging.debug(
                f'代理 {p} block 过多, {doubanGroup.redirectCount.get(p, 0)}, 重新获取 {times} 次'
            )
            p = getSmartProxy()
        logging.debug(f'成功: {p}')
        request.meta["proxy"] = p
        logging.debug(f'获取代理: {p} -> {request.url}')


class Redirect302Middleware(object):
    def process_response(self, request, response, spider):
        if response.status in [200]:
            return response
        elif response.status in [302, 403]:
            logging.debug(
                f'重定向或者403, reschedule 请求 💫💫💫💫💫💫💫💫................\n{request.url}'
            )
            proxy = request.meta.get('proxy', 'No proxy')
            blockCount = doubanGroup.redirectCount.get(proxy, 0)
            blockCount = blockCount + 1
            doubanGroup.redirectCount[proxy] = blockCount
            logging.debug(f'本次302/403代理: ip: {proxy}')
            if blockCount > 10:
                logging.info(
                    f'[代理失效]: 302/403 次数: {blockCount}, block 过多, 代理有毒! 🤬🤬🤬🤬🤬🤬🤬'
                )
            else:
                logging.debug(f'[代理失效]: 302/403 次数: {blockCount}')
            # meta = request.meta
            # delay = meta.get('302delay', 0)
            # delay = delay + 5
            # meta['302delay'] = delay
            return Request(request.url,
                           dont_filter=True,
                           headers=request.headers,
                           callback=request.callback,
                           meta=request.meta)
        elif response.status in [404]:
            return response
        else:
            return response


class RedirectDelayMiddleware(object):
    def process_request(self, request, spider):
        delay = request.meta.get('302delay', 0)
        if delay > 0:
            logging.debug(f'🌙🌙🌙🌙🌙之前302, 这次请求睡眠: {delay}: {request.url}')
            time.sleep(delay)
        return request
