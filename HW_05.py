import sys
from pymongo import MongoClient
from zeep import Client
from pprint import pprint

cur_char = 'GBP'
date_start = '2019-08-01'
date_end = '2019-08-07'

url = 'https://www.cbr.ru/DailyInfoWebServ/DailyInfo.asmx?WSDL'
client = Client(url)

curenum = client.service.EnumValutes(False)
cur_code = ''
for item in curenum._value_1._value_1:
    for d in item.values():
        #print(d['Vname'].strip(), d['VcharCode'], d['Vcode'].strip())
        if d['VcharCode'] == cur_char:
            cur_code = d['Vcode'].strip()

if cur_code == '':
    print("Валюта не существует")
    sys.exit(0)

curdin = client.service.GetCursDynamic(date_start, date_end, cur_code)
cur_list = []
for item in curdin._value_1._value_1:
    for d in item.values():
        date = d['CursDate']
        curs = str(d['Vcurs'])
        cur_list.append({'date': date, 'curs': curs})
        
print(cur_list)

mongo_client = MongoClient('mongodb://127.0.0.1:27017')
db = mongo_client[cur_char]
curdb = db[cur_char]
curdb.delete_many({})

try:
    result = curdb.insert_many(cur_list)
    print(result)
except Exception as e:
    print(e)

for i in curdb.find(): print(i)

mongo_client.close()

x = max(cur_list, key=lambda x: x['curs'])
max_date = x['date']
max_curs = float(x['curs'])

x = min(cur_list, key=lambda x: x['curs'])
min_date = x['date']
min_curs = float(x['curs'])

print(f'Валюту {cur_char} выгодно было купить {min_date.year}-{min_date.month}-{min_date.day},')
print(f'а продать {max_date.year}-{max_date.month}-{max_date.day}.')
print(f'Прибыль: {max_curs-min_curs}')



