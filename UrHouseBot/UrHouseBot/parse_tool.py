
import re
import random
from datetime import datetime

keyword = [
    '徐家汇',
    '湖南路',
    '上海图书馆',
    '武康路',
    '乌鲁木齐',
    '兴国路',
    '幸福路',
    '平武路',
    '镇宁路',
    '番禺路',
    '愚园路',
    '江苏路',
]

def appendRoad():
    keys =  keyword[0]
    for key in keyword[1:]:
        keys = keys + "|" + key
    return keys

def get_next_page_link(response):
    next = response.css('.next a::attr(href)').extract_first()
    print('下一页: ' + next)
    return next

def is_need_parse(date):
    if not re.search('.*\d{4}.*', date):
        date = str(datetime.now().year) + '-' + date
        dformat = format_date
    if re.search(".*:.*", date):
        dformat = format_dateTime
    delta_time = datetime.now() - datetime.strptime(date, dformat)
    return delta_time.days < 30

def random_cat():
    return str(random.randint(1, 50) + 1000)

def filter_title(title):
    restr = ".*{0}+.*".format(appendRoad())
    if re.search(restr, title):
        return True
    return False


format_dateTime = '%Y-%m-%d %H:%M'
format_date = '%Y-%m-%d'
