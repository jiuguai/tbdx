import logging
import redis

cookies = "thw=cn; enc=ZWcaGPmb814mOAQRFxtIGnsaXouiz7BVmJ4i4oZe3mpxbCV6q7pCborUvLZBe84a9wVC7Yef%2F9IrA1dzdz1eOQ%3D%3D; hng=CN%7Czh-CN%7CCNY%7C156; t=81f924a6459c4adefacb9fad5da3f530; cna=zCHQFjs6DVsCAd7wcizXMEpY; lgc=%5Cu96C60%5Cu6781; tracknick=%5Cu96C60%5Cu6781; mt=ci=14_1; cookie2=18c2cc39af38c8de685563c83259e6b1; _tb_token_=3aa3fa3853e9a; _m_h5_tk=33cc15cb349838496cdcbc6fe164c48a_1587641576653; _m_h5_tk_enc=ad0f03c8ef63605cae94610a85533c96; _samesite_flag_=true; sgcookie=EABAMomV8n1M2nWg8PbHh; unb=2187843634; uc1=existShop=false&cookie15=Vq8l%2BKCLz3%2F65A%3D%3D&pas=0&cookie21=W5iHLLyFeYTE&cookie16=URm48syIJ1yk0MX2J7mAAEhTuw%3D%3D&cookie14=UoTUPcqfHy2GrQ%3D%3D; uc3=vt3=F8dBxGR1S2lQ1%2FUbwZ0%3D&id2=UUkGVJHeIputLA%3D%3D&nk2=3zY0LDQ%3D&lg2=V32FPkk%2Fw0dUvg%3D%3D; csg=4a6dadda; cookie17=UUkGVJHeIputLA%3D%3D; dnk=%5Cu96C60%5Cu6781; skt=cfe31ae55be41255; existShop=MTU4NzYzMzMyMA%3D%3D; uc4=nk4=0%403cIrCkqmW75GQXyhmy8HJQ%3D%3D&id4=0%40U2uKc%2BNfWQRDgT3ckBVs21zUd6WH; _cc_=UtASsssmfA%3D%3D; _l_g_=Ug%3D%3D; sg=%E6%9E%814e; _nk_=%5Cu96C60%5Cu6781; cookie1=AQDJRq7KERyeA54kdBKvYSTlzCWFssLvmeqxKIpw6F4%3D; tfstk=cTxOBy2AKXcG0i9Nzn3hczL08QDhZLuOif1zDxNw1uqIDFEAi9xk2_4LfTFOvvC..; isg=BD8_wg-QXdfBHVk4T5LUZ1MczhPJJJPG_qZlk9EM2-414F9i2fQjFr3yIrAeo2s-; l=eBT96RbHQiKBuAgsBOfaFurza77OSIRYYuPzaNbMiT5PO7CB5AUPWZjXRVL6C3GVh602R3oekbNwBeYBqQAonxvTtdBHzUkmn"
token = list(filter(lambda x:x.startswith('_m_h5_tk='),cookies.replace(' ','').split(';')))[0].split('=')[1].split('_')[0]
app_key = "12574478"

LIMIT_ITEMS_COURSE = 500
LIMIT_ITEMS = 20

MYSQL_DIC = {
    "user":"root",
    "password":"jiuguai",
    "host":"localhost",
    "port":3306,
    "database":"tbdaxue",
    "charset" :"utf8mb4"
}


REDIS_CON = {
    'host':'127.0.0.1',
    'port':6379,
    'db':0,
    'decode_responses':True
}


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(filename)s [%(lineno)s] - %(levelname)s : %(threadName)s: %(message)s')
fh = logging.FileHandler('test.log',encoding='utf-8') 
fh.setFormatter(formatter)
logger.addHandler(fh)