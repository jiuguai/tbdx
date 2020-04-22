import asyncio
import sys
import time
import json
from hashlib import md5
from aiohttp import ClientSession, ClientTimeout, TCPConnector
import logging
import pymysql
import redis
from settings import cookies, token
def get_class_ids():
    MYSQL_DIC = {
        "user":"root",
        "password":"jiuguai",
        "host":"localhost",
        "port":3306,
        "database":"tbdaxue",
        "charset" :"utf8mb4"
    }

    conn = pymysql.connect(**MYSQL_DIC)
    cursor = conn.cursor()
  

    sql = "select DISTINCT class_id from t_video "
    cursor.execute(sql)
    result = cursor.fetchall()
    conn.close()
    return [x[0] for x in result]






logger = logging.getLogger()
formatter = logging.Formatter('%(asctime)s %(filename)s [%(lineno)s] - %(levelname)s : %(threadName)s: %(message)s')
fh = logging.FileHandler('test.log',encoding='utf-8') 

fh.setFormatter(formatter)
logger.addHandler(fh)
count = 0

async def save_class_detail(r_con,reverse_save=False):

    global count
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
        "cache-control": "no-cache",
        "cookie": cookies,
        "pragma": "no-cache",
        "referer": "https://idaxue.taobao.com/chapter/content.jhtml?spm=a1z14.13878553.3865578915.1.3ae477d8CF5nOe&labelIds=44002&acm=lb-zebra-602945-7747382.1003.4.7192208&scm=1003.4.lb-zebra-602945-7747382.OTHER_15768048017001_7192208",
        "sec-fetch-dest": "script",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4115.5 Safari/537.36"
    }


    url = "https://h5api.m.taobao.com/h5/mtop.taobao.tbdx.learn.wireless.class.detail/1.0/"
    o = "12574478"

    if reverse_save:
        sname1 = 'class:id_r'
        sname2 = 'class:id'
    else:
        sname1 = 'class:id'
        sname2 = 'class:id_r'

    class_id = r_con.spop(sname1)

    while class_id:

        search_data = {
            'classId':int(class_id)
        }

        search_data = json.dumps(search_data)
        s = str(int(time.time() * 1000 // 1))

        
        key = token + "&" + s + "&" + o + "&" +search_data
        sign = md5(key.encode('utf-8')).hexdigest()
        params = {
            'jsv': '2.4.16',
            'appKey': '12574478',
            't': s,
            'sign':sign,
            'api': 'mtop.taobao.tbdx.learn.wireless.class.detail',
            'type': 'jsonp',
            'v': '1.0',
            'dataType': 'jsonp',
            'callback': 'mtopjsonp7',
            'data': search_data
            

        }

        timeout = ClientTimeout(total=10)
        async with ClientSession(timeout=timeout) as session:
            try:
                async with session.get(url ,headers=headers, params=params) as resp:


                    txt = await resp.text()
                    js = json.loads(txt[12:-1])
                    if len(js['data']) != 0:
                        r_con.hset("class:details",class_id,txt[12:-1])
                        count += 1
                        print("%s %s" %(count, class_id))
                    else:
                        
                        if js['ret'][0].startswith('FAIL_SYS_TOKEN_EXOIRED'):
                            print('口令过期')
                            sys.exit()
                        elif not js['ret'][0].startswith('SUCCESS'):
                            r_con.sadd(sname2,class_id)
                        logger.warning("%s\n%s" %(class_id,js))
                    
            except asyncio.TimeoutError:
                r_con.sadd(sname1, class_id)
                logger.warning("%s 超时" %class_id)


        class_id = r_con.spop(sname1)

def save_mysql(class_details):
    MYSQL_DIC = {
        "user":"root",
        "password":"jiuguai",
        "host":"localhost",
        "port":3306,
        "database":"tbdaxue",
        "charset" :"utf8mb4"
    }

    conn = pymysql.connect(**MYSQL_DIC)
    cursor = conn.cursor()
    sql = """insert into 
        class_details(class_id, class_name, ww_id, org_name, lecturer, assistant,
        video_num,student_num
        ) 
        values(%s, %s, %s, %s, %s, %s, %s, %s)

    """

    data_l = []
    for class_id, c_detail in class_details.items():
        js = json.loads(c_detail)
        if len(js['data']):
            r = js['data']['model']
            ww_id = r['assistant'][0].get('nick', None)
            orgName = r.get('orgName',"")
            lecturer = ','.join([ass['name'] for ass in r['lecturer']])
            assistant = ','.join([ass['name'] for ass in r['assistant']])
            video_num = r.get('sectionNum', 0)
            stu_num = r.get('studentNum', 0)

            l = [int(class_id), r.get('className',''),ww_id,orgName,lecturer,assistant,video_num, stu_num]
            data_l.append(l)
            print(ww_id)
        if len(data_l) > 99:
            cursor.executemany(sql,data_l)
            conn.commit()
            data_l = []


    if len(data_l):
        cursor.executemany(sql,data_l)
        conn.commit()
    conn.close()

if __name__ == '__main__':
    COROUTINE_MAX = 60
    reverse_save = False
    REDIS_ATTR_DIC = {
        "host":'127.0.0.1',
        "port":6379,
        "db":0,
        "decode_responses":True  #设置为True返回的数据格式就是时str类型
    }


    r_con = redis.Redis(**REDIS_ATTR_DIC)
    r_con.delete('class:id*',"class:details")
    
    data = get_class_ids()

    r_con.sadd('class:id',*data)
    
    while r_con.scard('class:id') != 0 or r_con.scard('class:id_r') != 0:
        loop = asyncio.get_event_loop()
        tasks = []
        for i in range(COROUTINE_MAX):
            tasks.append(save_class_detail(r_con,reverse_save))
        loop.run_until_complete(asyncio.wait(tasks))

        reverse_save = not reverse_save
        time.sleep(3)

    class_details = r_con.hgetall('class:details')


    save_mysql(class_details)


