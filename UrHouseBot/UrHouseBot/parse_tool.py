import re
import random
from datetime import datetime
import json
import logging

limitTime = 7

regions = [
    '龙华',
    '龙华中路',
    '东安',
    '13号',
    '世博会博物馆',
    '成山路',
    # '长寿路',
    '零陵',
    '斜土',
    '鲁班',
    '西木',
    '大木桥',
    '小木桥',
    # '绿地',
    '绿地缤纷',
    '蒙自路',
    '瞿溪路',
    '鲁中小区',
    '汇暻生活广场',
    '瞿溪坊',
    '德福苑',
    '南园大厦',
    '东安',
    '茶陵',
    '嘉善路',
    '江苏路',
    '静安寺',
    # '金沙江路',
    '长清路'
]

conditions = [
    '菜市场',
    '菜场',
    '地铁',
    "一室户",
  "独卫",
  "独用",
]

avoids = {
    "title": [
        '限女生', '限女', '限妹', '限一个妹',
        '已出租',
        '城家',
        '公寓',
        '求租',
        '已经租',
        '精装'
    ],
    "content":
    [
      '限女生', '限女', '限妹', '限一个妹',
     '已出租', '城家', '公寓', '求租', '已经租', '精装']
}

banFrom = [
    '啦啦啦啦',
]

def getRegions():
    data = regions
    try:
        with open('./regions.json', 'r') as f:
            try:
                data = json.load(f)
            except:
                logging.debug('regions文件错误')
    except:
        logging.debug('没有regions文件')
        with open('./regions.json', 'w') as f:
            json.dump(data, f)
    return list(set(data))


def getAvoids(use='title'):
    data = avoids
    try:
        with open('./avoids.json', 'r') as f:
            try:
                data = json.load(f)
            except:
                logging.debug('avoid文件错误')
    except:
        logging.debug('没有avoid文件')
        with open('./avoids.json', 'w') as f:
            json.dump(data, f)
    return list(set(data[use]+data['content']))


def appendKeys(dicts):
    keys = dicts[0]
    for key in dicts[1:]:
        keys = keys + "|" + key
    return keys


def get_next_page_link(response):
    next = response.css('.next a::attr(href)').extract_first()
    # logging.debug('下一页: ' + next)
    return next


format_dateTime = '%Y-%m-%d %H:%M'
format_date = '%Y-%m-%d'
format_dateTimed = '%Y-%m-%d %H:%M:%S'


def is_need_parse(date, limit=limitTime):
    if re.search('.*天.*', date):
        return True
    if not re.search('.*\d{4}.*', date):
        date = str(datetime.now().year) + '-' + date
        dformat = format_date
    if re.search('.*\d{4}-\d{1,2}-', date):
        dformat = format_date
    if re.search(".*:.*", date):
        dformat = format_dateTime
    if re.search(".*:\d{2}:.*", date):
        dformat = format_dateTimed
    delta_time = datetime.now() - datetime.strptime(date, dformat)
    return delta_time.days < limit


def random_cat():
    return str(random.randint(1, 50) + 1000)



def filter_title(content, title=None, link=None, use='title'):
    content = content.strip()
    re_region = "{0}+".format(appendKeys(getRegions()))
    match = re.findall(re_region, content)
    if match:
        re_avoid = '{0}+'.format(appendKeys(getAvoids(use)))
        avoid_match = re.findall(re_avoid, content)
        if avoid_match:
            am = list(set(avoid_match))
            logging.debug(f'❌❌❌❌❌❌击中屏蔽词: {am} -> {title} -> {link}')
            return (False, am)
        else:
            return (True, list(set(match)))
    return (False, [])


def filter_ur_need(content):
    re_need = ".*{0}+.*".format(appendKeys(conditions))
    match = re.search(re_need, content)
    if match:
        return match.group()
    return False
