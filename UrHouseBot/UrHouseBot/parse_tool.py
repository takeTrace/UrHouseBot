
import re
import random
from datetime import datetime


def get_next_page_link(self, response):
    next = response.css('.next a::attr(href)').extract_first()
    print('下一页: ' + next)
    return next

def is_need_parse(self, response):
    date = response.css('tbody .time').extract_first()
    delta_time = datetime.now() - datetime.strptime(date, '%m-%d %h:%s')
    return delta_time.days < 30

def random_cat(self):
    return random.randint(1, 50) + 1000