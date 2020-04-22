from copy import deepcopy
import re
import json
import time
import sys

import requests
from hashlib import md5
import pandas as pd
import numpy as np
import pymysql

from settings import cookies, token



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


# 获取分类
url ="https://idaxue.taobao.com/chapter/label/getChapterCategoryLabel"
rep = requests.get(url, headers=headers)
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




MYSQL_MALL_DIC = {
    "user":"root",
    "password":"jiuguai",
    "host":"localhost",
    "port":3306,
    "database":"tbdaxue",
    "charset" :"utf8mb4"
}

conn = pymysql.connect(**MYSQL_MALL_DIC)
cursor = conn.cursor()


url = "https://h5api.m.taobao.com/h5/mtop.taobao.tbdx.learn.index.chapter.search.with.label/1.0/"

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
count = 0
ids = set()
count = 0
o = "12574478"
limit = 500
max_page = 10
columns = ['category', 'chapter', 'class_id', 'class_student_num', 'fee', 'org_name', 'title', 'v_id']
sql = "insert into t_video(%s) values(%s)" %(','.join(columns),','.join(np.repeat('%s',len(columns))))

start_t = time.time()
for label_id, label in label_ids.items():
    for chapter_type in ['TBLIVE','RECORDED_BROADCAST']:
        for fee in [2 ,3]:
            for page in range(1,max_page+1):
                search_data = {
                    'labelIds': label_id,
                     'classSearchSort': 0,
                     'fee': fee,
                     'chapterTypeEnum': chapter_type,
                     'currPageNo':page,
                     'limit': limit,
                     'keyword': ''
                }
                search_data = json.dumps(search_data)
                s = str(int(time.time() * 1000 // 1))
                key = token + "&" + s + "&" + o + "&" +search_data
                sign = md5(key.encode('utf-8')).hexdigest()
                params = {
                    'jsv': '2.5.8',
                    'appKey': '12574478',
                    't': s,
                    'sign':sign,
                    'api': 'mtop.taobao.tbdx.learn.index.chapter.search.with.label',
                    'type': 'jsonp',
                    'v': '1.0',
                    'dataType': 'jsonp',
                    'callback': 'mtopjsonp7',
                    'data': search_data
                }
                
                rep = requests.get(url,headers=headers,params=params)
                js = json.loads(rep.text[12:-1])
                

                if len(js['data']) != 0 :
                    if js['ret'][0].startswith('FAIL_SYS_TOKEN_EXOIRED'):
                        print('口令过期')
                        sys.exit()
                    datas  = js['data']['model']['datas']
                    ds = []
                    for data in datas:
                        temp = {
                            "v_id":data['id'],
                            "class_id":data['modelId'],
                            "org_name":data['orgName'],
                            "title":data['title'],
                            "class_student_num":data['classStudentNum'],
                            "chapter":",".join(data['chapterLabelList']),
                            "fee":data["classTypeEnum"],
                            "category":label

                        }
                        ds.append(temp)
                    df = pd.DataFrame(ds)
                    l = []
                    for i,row in df[columns].iterrows():
                        l.append(row.tolist())

                    cursor.executemany(sql,l)
                    conn.commit()
                    count += len(datas)
                    print('%s %s %s: %s' %(label,chapter_type, fee,len(datas)))
#                     print('\r%s' %count,end="")
                    if len(datas) < limit:
                        break
                else:
                    break
conn.close()
print(time.time() - start_t)