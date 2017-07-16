
import re
import random
from datetime import datetime

regions = [
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
    '地铁'
]

conditions = [
    '菜市场',
    '菜场',
    '地铁'
]

avoids = [
    '限女生',
    '已出租'
]

def appendKeys(dicts):
    keys =  dicts[0]
    for key in dicts[1:]:
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
    if re.search(".*:\d{2}:.*", date):
        dformat = format_dateTimed
    delta_time = datetime.now() - datetime.strptime(date, dformat)
    return delta_time.days < 30



def random_cat():
    return str(random.randint(1, 50) + 1000)

def filter_title(content):
    re_region = ".*{0}+.*".format(appendKeys(regions))
    match = re.search(re_region, content)
    if match:
        re_avoid = '.*{0}+.*'.format(appendKeys(avoids))
        avoid_match = re.search(re_avoid, content)
        if avoid_match:
            return False
        else:
            return match.group()
    return False

def filter_ur_need(content):
    re_need = ".*{0}+.*".format(appendKeys(conditions))
    match = re.search(re_need, content)
    if match:
        return match.group()
    return False


format_dateTime = '%Y-%m-%d %H:%M'
format_date = '%Y-%m-%d'
format_dateTimed = '%Y-%m-%d %H:%M:%S'