import asyncio
from copy import deepcopy
import re
import json
import time
import sys


import requests
from hashlib import md5

import pymysql
from aiohttp import ClientSession, ClientTimeout, TCPConnector

from settings import *

class ExtrClassId():

    def __init__(self,redis_con):
        self.redis_con = redis_con
        self.v_count = 0
        self.headers = headers = {
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

    def get_search_label(self):
        # 获取分类
        url ="https://idaxue.taobao.com/chapter/label/getChapterCategoryLabel"
        rep = requests.get(url, headers=self.headers)

        cl = rep.json()
        cl_data = cl['data']

        cl_ids = {d['id']:{'name':d['name'],'labelIds':d['parentIdTree'][1:-1].replace('|',',')} for d in cl_data}
        for i, d in cl_ids.items():
            label = []
            for label_id in d['labelIds'].split(','):
                label.append(cl_ids[int(label_id)]['name'])
            d['class'] = ','.join(label)
        


        # 处理分类
        cl_level = {
            1:set({}),
            2:set({}),
            3:set({}),
            4:set({})
        }

        for d in cl_data:
            cl_level[d['treeLevel']].add(d['parentId'])
        for i in range(2,len(cl_level) + 1):
            for parent_id in cl_level[i]:
                del cl_ids[parent_id]
        label_ids = {d['labelIds']:d['class'] for i,d in cl_ids.items()}

        return label_ids


    def save_search_params(self,label_ids):
        

        ''' 
            labelIds : 
                44001 -> 新手入门
                44002 -> 电商基础
                44003 -> 电商进阶
                42001 -> 跨境电商
                
            chapterTypeEnum:
                TBLIVE -> 直播课
                RECORDED_BROADCAST -> 录播课
            fee:
                3 -> 免费
                2 -> 付费
        '''

        
        self.redis_con.delete('class:search')
        self.redis_con.delete('class:search_r')
        for label_id, label in label_ids.items():
            for chapter_type in ['TBLIVE','RECORDED_BROADCAST']:
                for fee in [2 ,3]:
                    search_data = {
                            'labelIds': label_id,
                             'classSearchSort': 0,
                             'fee': fee,
                             'chapterTypeEnum': chapter_type,
                             'currPageNo':1,
                             'limit': LIMIT_ITEMS,
                             'keyword': ''
                    }
                    search_data = json.dumps(search_data)
                    t = str(int(time.time() * 1000 // 1))
                    key = token + "&" + t + "&" + app_key + "&" +search_data
                    sign = md5(key.encode('utf-8')).hexdigest()
                    params = {
                        'jsv': '2.5.8',
                        'appKey': app_key,
                        't': t,
                        'sign':sign,
                        'api': 'mtop.taobao.tbdx.learn.index.chapter.search.with.label',
                        'type': 'jsonp',
                        'v': '1.0',
                        'dataType': 'jsonp',
                        'callback': 'mtopjsonp7',
                        'data': search_data
                    }
                    print('params save %s' %(label_ids.get(label_id,"")))
                    data = {"label":"%s,%s,%s" %(label_ids[label_id],chapter_type,fee),"params":params}
                    self.redis_con.lpush('class:search',json.dumps(data))
                    

    def ext_course_classids(self):
        url = "https://h5api.m.taobao.com/h5/mtop.taobao.tbdx.class.search/1.0/"

        i = 1
        class_ids = set({})
        while True:
            search_data = {
                'classSerachSort': '2',
                 'categoryTagId': None,
                 'contentTagId': None,
                 'groupTagId': None,
                 'currPageNo': i,
                 'limit': 500
            }

            search_data = json.dumps(search_data)

            t = str(int(time.time() * 1000 // 1))
            app_key = '12574478'
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
            


            rep = requests.get(url,headers=self.headers, params=params)
            js = json.loads(rep.text[12:-1])

            print('course -- %s page' %i)
            i += 1
            if len(js['data']) and len(js['data']['model']['datas']):
                ds = js['data']['model']['datas']
                class_ids = class_ids|{x['id'] for x in js['data']['model']['datas']}
                if len(ds) < LIMIT_ITEMS:
                    break
            else:
                break

        self.redis_con.sadd('class:ids', *class_ids)


    async def ext_class_id(self,  reverse_save=False):
        
        url = "https://h5api.m.taobao.com/h5/mtop.taobao.tbdx.learn.index.chapter.search.with.label/1.0/"
        if reverse_save:
            lname1 = 'class:search_r'
            lname2 = 'class:search'
        else:
            lname1 = 'class:search'
            lname2 = 'class:search_r'
        

        timeout = ClientTimeout(total=10)
        while self.redis_con.llen(lname1):

            data = self.redis_con.rpop(lname1)

            data = json.loads(data)
            search_key = data['label']
            params = data['params']


            async with ClientSession(timeout=timeout) as session:

                try:
                    async with session.get(url ,headers=self.headers, params=params) as resp:


                        txt = await resp.text()
                        js = json.loads(txt[12:-1])
                        if len(js['data']) != 0:
                            r = js['data']['model']['datas']
                            class_ids = {x['modelId'] for x in r}
                            if class_ids:
                                self.redis_con.sadd('class:ids', *class_ids)
                            if len(r) == LIMIT_ITEMS:
                                search_data = json.loads(data['params']['data'])
                                search_data['currPageNo'] += 1
                                
                                search_data = json.dumps(search_data)
                                t = str(int(time.time() * 1000 // 1))
                                key = token + "&" + t + "&" + app_key + "&" +search_data
                                sign = md5(key.encode('utf-8')).hexdigest()
                                data['params']['t'] = t
                                data['params']['sign'] = sign
                                data['params']['data'] = search_data


                                
                                self.redis_con.lpush(lname1,json.dumps(data))
                            self.v_count += len(r)
                            print("v_count:%s  s_key:%s" %(self.v_count,search_key))
                        else:
                            ret = js['ret'][0]
                            if ret.startswith('FAIL_SYS_TOKEN_EXOIRED'):
                                print('口令过期')
                                sys.exit()
                            elif ret.startswith('FAIL_SYS_ILLEGAL_ACCESS'):
                                logger.error('%s \n%s'%(ret,data))

                            elif not ret.startswith('SUCCESS'):
                                self.redis_con.lpush(lname2,json.dumps(data))
                            elif ret.startswith('SUCCESS'):
                                logger.warning("%s \n%s" %(search_key,params), )

                except asyncio.TimeoutError:
                    self.redis_con.lpush(lname2,json.dumps(data))

            


    def __call__(self, **kargs):

        self.save_search(**kargs)

    def save_search(self, coroutine_max = 30, sleep_time=1.5):
        self.redis_con.delete(
            'class:ids',
            'class:ids_r',
            'class:details', 
            "class:future"
            )
        label_ids = self.get_search_label()
        self.save_search_params(label_ids)
        
        reverse_save = False
        while self.redis_con.llen('class:search') != 0 or self.redis_con.llen('class:search_r') !=0:
            loop = asyncio.get_event_loop()
            tasks = []
            for i in range(coroutine_max):
                tasks.append(self.ext_class_id(reverse_save))
            loop.run_until_complete(asyncio.wait(tasks))
            reverse_save = not reverse_save
            time.sleep(sleep_time)


        print('提取course中classId')
        self.ext_course_classids()


#

class ExtractClassDetail():
    def __init__(self,redis_con):
        self.redis_con = redis_con


        self.class_count = 0

        self.headers = {
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

    async def save_class_detail(self,reverse_save=False):

        url = "https://h5api.m.taobao.com/h5/mtop.taobao.tbdx.learn.wireless.class.detail/1.0/"
       

        if reverse_save:
            sname1 = 'class:ids_r'
            sname2 = 'class:ids'
        else:
            sname1 = 'class:ids'
            sname2 = 'class:ids_r'

        class_id = self.redis_con.spop(sname1)

        while class_id:

            search_data = {
                'classId':int(class_id)
            }

            search_data = json.dumps(search_data)
            s = str(int(time.time() * 1000 // 1))

            
            key = token + "&" + s + "&" + app_key + "&" +search_data
            sign = md5(key.encode('utf-8')).hexdigest()
            params = {
                'jsv': '2.4.16',
                'appKey': app_key,
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
                    async with session.get(url ,headers=self.headers, params=params) as resp:


                        txt = await resp.text()
                        js = json.loads(txt[12:-1])
                        if len(js['data']) != 0:
                            self.redis_con.hset("class:details",class_id,txt[12:-1])
                            self.class_count += 1
                            print("%s 获取class_id:%s 详情" %(self.class_count, class_id))
                        else:
                            ret = js['ret'][0]
                            if ret.startswith('FAIL_SYS_TOKEN_EXOIRED'):
                                print('口令过期')
                                sys.exit()
                            elif ret.startswith('FAIL_SYS_ILLEGAL_ACCESS'):
                                logger.error('%s \n%s'%(ret,data))
                            elif not ret.startswith('SUCCESS'):
                                self.redis_con.sadd(sname2,class_id)
                            elif ret.startswith('SUCCESS'):
                                self.redis_con.sadd('class:future',class_id)
                                logger.warning("%s\n%s" %(class_id,js))
                        
                except asyncio.TimeoutError:
                    self.redis_con.sadd(sname1, class_id)
                    logger.warning("%s 超时" %class_id)


            class_id = self.redis_con.spop(sname1)

    def save_mysql(self, class_details):

        conn = pymysql.connect(**MYSQL_DIC)
        cursor = conn.cursor()
        sql = """insert into 
            class_details(class_id, class_name, ww_id, org_name, lecturer, assistant,
            video_num,student_num
            ) 
            values(%s, %s, %s, %s, %s, %s, %s, %s)

        """
        cursor.execute('delete from class_details')
        conn.commit()
        count = 0
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
                
            if len(data_l) > 99:
                cursor.executemany(sql,data_l)
                conn.commit()
                count += len(data_l)
                print('save: %s' %count)
                data_l = []


        if len(data_l):
            cursor.executemany(sql,data_l)
            conn.commit()
            count += len(data_l)
            print('save: %s' %count)
            
        conn.close()

    def __call__(self, **kargs):
        self.save(**kargs)

    def save(self, coroutine_max = 60, sleep_time=1.5):
        
        reverse_save = False

        while self.redis_con.scard('class:ids') != 0 or self.redis_con.scard('class:ids_r') != 0:
            loop = asyncio.get_event_loop()
            tasks = []
            for i in range(coroutine_max):
                tasks.append(self.save_class_detail(reverse_save))
            loop.run_until_complete(asyncio.wait(tasks))

            reverse_save = not reverse_save
            time.sleep(sleep_time)

        class_details = self.redis_con.hgetall('class:details')

        print('存入数据库')
        self.save_mysql(class_details)



    

def run():
    redis_con = redis.Redis(**REDIS_CON)

    # 获取搜索classId
    ExtrClassId(redis_con )(coroutine_max = 30)
    ExtractClassDetail(redis_con )(coroutine_max = 80)


if __name__ == '__main__':
    
    redis_con = redis.Redis(**REDIS_CON)

    # 获取搜索classId
    ExtrClassId(redis_con)()
    ExtractClassDetail(redis_con)()

# conn = pymysql.connect(**MYSQL_MALL_DIC)
# cursor = conn.cursor()