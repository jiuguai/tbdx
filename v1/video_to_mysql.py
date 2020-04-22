
import json

import redis


import pymysql
def save_mysql(r_con):
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
    sql = """
    insert into t_video(v_id, class_id, org_name, title, class_student_num,category)
     values(%s,%s,%s,%s,%s,%s)
    """
    data_l = []
    for class_id in r_con.hkeys('video:ids'):
        item = r_con.hget('video:ids',class_id)
        
        item = json.loads(item)
        print(class_id)
        class_id = int(class_id)
        l = [class_id,class_id,item['organizationVO']['name'],item['chapterName'],
         int(item['studentNum']),item['category']
         ]

        data_l.append(l)
        print(class_id)
        if len(data_l)>99:
            cursor.executemany(sql,data_l)
            conn.commit()
            data_l = []
    
    if len(data_l):
        cursor.executemany(sql,data_l)

    conn.commit()

    conn.close()
    
    



if __name__ == '__main__':

    REDIS_CON = {
            'host':'127.0.0.1',
            'port':6379,
            'db':0,
            'decode_responses':True
        }


    r_con = redis.Redis(**REDIS_CON)

    l = r_con.hkeys("video:details")
    count = 0 
    print('--------> 去重')
    for search_key in l:
        data = r_con.hget('video:details',search_key)
        data = json.loads(data)
        data = data['data']['model']['datas']
        count += len(data)
        print(search_key)
        for item in data:
            if not r_con.hexists('video:ids',item['id']):
                item['category'] = search_key
                r_con.hset("video:ids",item['id'],json.dumps(item))
    
    print('-'*20, count)
    save_mysql(r_con)   
                