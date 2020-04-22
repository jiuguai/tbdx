import logging
import redis

cookies = "thw=cn; enc=ZWcaGPmb814mOAQRFxtIGnsaXouiz7BVmJ4i4oZe3mpxbCV6q7pCborUvLZBe84a9wVC7Yef%2F9IrA1dzdz1eOQ%3D%3D; hng=CN%7Czh-CN%7CCNY%7C156; t=81f924a6459c4adefacb9fad5da3f530; cna=zCHQFjs6DVsCAd7wcizXMEpY; lgc=%5Cu96C60%5Cu6781; tracknick=%5Cu96C60%5Cu6781; mt=ci=14_1; cookie2=1fda1c65809efe4d0669d30e6a3807f0; _tb_token_=e3b7beb5ed51b; _samesite_flag_=true; dnk=%5Cu96C60%5Cu6781; _m_h5_tk=9a38415dafbb6a0f67b209683dc6351f_1587571214494; _m_h5_tk_enc=da645b8ec2de8307920cf1829b80091c; sgcookie=Eck9GjhJAnDdlUWeAQKLB; unb=2187843634; uc1=cookie21=URm48syIYB%2Fc&cookie16=Vq8l%2BKCLySLZMFWHxqs8fwqnEw%3D%3D&pas=0&cookie15=WqG3DMC9VAQiUQ%3D%3D&cookie14=UoTUPcln85oLmQ%3D%3D&existShop=false; uc3=nk2=3zY0LDQ%3D&id2=UUkGVJHeIputLA%3D%3D&lg2=UtASsssmOIJ0bQ%3D%3D&vt3=F8dBxGR2UmNkPsWDSeA%3D; csg=fff2be1d; cookie17=UUkGVJHeIputLA%3D%3D; skt=179b6c82e3577cf4; existShop=MTU4NzU2MjU4MQ%3D%3D; uc4=id4=0%40U2uKc%2BNfWQRDgT3ckBVs2Jhciett&nk4=0%403cIrCkqmW75GQX%2BQENukwQ%3D%3D; _cc_=W5iHLLyFfA%3D%3D; _l_g_=Ug%3D%3D; sg=%E6%9E%814e; _nk_=%5Cu96C60%5Cu6781; cookie1=AQDJRq7KERyeA54kdBKvYSTlzCWFssLvmeqxKIpw6F4%3D; tfstk=cKtPBA_4Q0nrfcivWgIFFAzE7R7RZ7KHfqWdrFz5BBZSbObli8Ndn74DgCCtmaf..; l=eBT96RbHQiKBuRF6BO5aPurza77T0IRb8sPzaNbMiIHca69F9FT4-NQcDHdkWdtjgt5V2etrYEh7_RHyJPU38EweqVxbuVas-wp68e1..; isg=BPj4Fhvt0vsi_z6NbPfrWuAxyaaKYVzr7RvCRjJp3zPmTZk32nHFehArBUV9HRTD"
token = list(filter(lambda x:x.startswith('_m_h5_tk='),cookies.replace(' ','').split(';')))[0].split('=')[1].split('_')[0]
app_key = "12574478"


LIMIT_ITEMS = 500

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
formatter = logging.Formatter('%(asctime)s %(filename)s [%(lineno)s] - %(levelname)s : %(threadName)s: %(message)s')
fh = logging.FileHandler('test.log',encoding='utf-8') 
fh.setFormatter(formatter)
logger.addHandler(fh)