import asyncio
import re
import json
import time
import logging
from hashlib import md5

import requests
import redis
from aiohttp import ClientSession, ClientTimeout, TCPConnector

from settings import cookies, token

def save_search_data(r_con):

    url = "https://taobaodaxue.taobao.com/wow/daxue/act/kechengzhongxing"
    rep  = requests.get(url)

    txt = rep.text
    r = re.search('{"useAsyncRender":.+',txt)
    if r:
        js = json.loads(r.group())

    data = js['data']
    item = data[list(data.keys())[0]]['item']
    r_con.delete('request:search_data')
    for category in item['items_category']:
        for content in item['items_content']:
            for group in item['items_group']:
                
                key = ','.join([category['item_name'], content['item_name'], group['item_name']])
                search_data = {
                    'classSerachSort': '2',
                     'categoryTagId':category['item_categorytagid'],
                     'contentTagId': content['item_contenttagid'],
                     'groupTagId': group['item_grouptagid'],
                     'currPageNo': 1,
                     'limit': 500
                }

                data = {
                    'key':key,
                    'data':search_data,
                    'retry':0
                }
                search_data = json.dumps(data)
                print(key)
                r_con.lpush('request:search_data',search_data)

logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(filename)s [%(lineno)s] - %(levelname)s : %(threadName)s: %(message)s')
fh = logging.FileHandler('test.log',encoding='utf-8') 
fh.setFormatter(formatter)
logger.addHandler(fh)

count = 0
async def save_result(r_con, reverse_save=False):
    global count
    url = "https://h5api.m.taobao.com/h5/mtop.taobao.tbdx.class.search/1.0/"

    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "cache-control": "no-cache",
        "cookie": cookies,
        "pragma": "no-cache",
        "referer": "https://idaxue.taobao.com/chapter/content.jhtml",
        "sec-fetch-dest": "script",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4115.5 Safari/537.36"
    }

    app_key = '12574478'

    if reverse_save:
        lname1 = 'request:search_data_err'
        lname2 = 'request:search_data'
    else:
        lname1 = 'request:search_data'
        lname2 = 'request:search_data_err'
        

    while r_con.llen(lname1) :
        data_s = r_con.rpop(lname1)
        data = json.loads(data_s)
        search_key = data['key']
        search_data = data['data']
        search_data = json.dumps(search_data)

        t = str(int(time.time() * 1000 // 1))
        
        key = token + "&" + t + "&" + app_key + "&" +search_data
        sign = md5(key.encode('utf-8')).hexdigest()

        params = {
            'jsv': '2.4.16',
            'appKey': app_key,
            't': t,
            'sign': sign,
            'api': 'mtop.taobao.tbdx.class.search',

            'v': '1.0',
            'preventFallback': 'true',
            'type': 'jsonp',
            'dataType': 'jsonp',
            'callback': 'mtopjsonp5',
            'data': search_data
        }

        timeout = ClientTimeout(total=8)
        async with ClientSession(timeout=timeout) as session:

            try:
                async with session.get(url ,headers=headers, params=params) as resp:


                    txt = await resp.text()
                    js = json.loads(txt[12:-1])
                    if len(js['data']) != 0:
                        r_con.hset("video:details",search_key,txt[12:-1])
                        count += 1
                        print(count,search_key)
                    else:
                        ret = js['ret'][0]
                        if ret.startswith('FAIL_SYS_TOKEN_EXOIRED'):
                            print('口令过期')
                            sys.exit()
                        elif not ret.startswith('SUCCESS'):

                            if data['retry'] < 3:
                                data['retry'] += 1
                                r_con.lpush(lname1,json.dumps(data))
                            else:
                                logger.warning("%s \n%s" %(search_key,js), )
                                data['retry'] = 0
                                r_con.lpush(lname2,json.dumps(data))
                        elif ret.startswith('SUCCESS'):
                            logger.warning("%s \n%s" %(search_key,js), )

            except asyncio.TimeoutError:
                r_con.lpush(lname1,json.dumps(data))



if __name__ == '__main__':

    REDIS_CON = {
        'host':'127.0.0.1',
        'port':6379,
        'db':0,
        'decode_responses':True
    }


    r_con = redis.Redis(**REDIS_CON)


    save_search_data(r_con)
    print('\n\n获取数据')
    lname1 = 'request:search_data'
    lname2 = 'request:search_data_err'
    flag = False
    while r_con.llen('request:search_data') != 0 or r_con.llen('request:search_data_err') !=0:
        loop = asyncio.get_event_loop()
        tasks = []
        for i in range(80):
            tasks.append(save_result(r_con, flag))
        loop.run_until_complete(asyncio.wait(tasks))
        flag = not flag
        time.sleep(3)
    
