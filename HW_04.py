import re, sys, requests
from time import sleep
from random import randint
from bs4 import BeautifulSoup
from pprint import pprint
from pymongo import MongoClient


vac_name = 'Программист'
vac_location = 'Санкт-Петербург'
depth = 1

headers = {'User-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'}
hh_link = 'https://hh.ru/search/vacancy?text={0} {1}'
sj_link = 'https://www.superjob.ru/vacancy/search/?geo[c][0]=1&keywords={0} {1}'

def get_vac_dict(name, location, salary, href):
    dct = {}
    dct['name'] = name
    dct['loc'] = location
    dct['sal'] = salary
    dct['href'] = href
    return dct

def get_salary(salary):
    if re.search('\d', salary) is None: return None
    salary = salary.replace(' ', '')
    salary = salary.replace('\xa0', '')
    match = re.findall('(\d+)[-|—]?(\d+)?(.*)', salary)[0]
    #print(match)
    min_salary = match[0]
    min_salary = int(min_salary) 
    max_salary = 0
    if len(match) >= 2:
        max_salary = match[1]
        max_salary = int(max_salary) if max_salary else 0
    if max_salary == 0: max_salary = min_salary
    currency = ''
    if len(match) == 3:
        currency = match[2]
    return min_salary, max_salary, currency

def parse_hh_vacancy(html):
    tmp = html.find('a', {'class': 'bloko-link HH-LinkModifier'})
    if tmp is None: return None
    vac_name = tmp.text
    vac_href = re.findall('^(.+)\\?', tmp.get('href'))[0]
    tmp = html.find('div', {'class': 'vacancy-serp-item__compensation'})
    vac_salary = get_salary(tmp.text) if tmp is not None else '' 
    if vac_salary is None: vac_salary = ''
    tmp = html.find('span', {'class': 'vacancy-serp-item__meta-info'})
    vac_location = tmp.text if tmp is not None else ''
    return get_vac_dict(vac_name, vac_location, vac_salary, vac_href)

def get_hh_vacancies(link, depth, delay=True):
    vacs = []
    for i in range(depth):
        if i == 0:
            req = requests.get(link, headers=headers)
        else:
            req = requests.get(link + '&page=' + str(i), headers=headers)
        if req.status_code != 200: break

        #with open(f'test{i}.html', 'w', encoding='utf-8') as f:
        #    f.write(req.text)
        
        soup = BeautifulSoup(req.text, 'html.parser')
        vac_html = soup.find('div', {'class': 'vacancy-serp'})
        if delay: sleep(randint(3, 5))

        for vac in vac_html.findChildren('div' , recursive=False):
            dct = parse_hh_vacancy(vac)
            if dct is None: continue
            vacs.append(dct)
    return vacs

def parse_sj_vacancy(html):
    tmp = html.find('div', {'class': '_3mfro CuJz5 PlM3e _2JVkc _3LJqf'})
    if tmp is None: return None
    vac_name = tmp.text
    #print(vac_name)
    tmp = html.find('a', {'class': '_1QIBo'})
    if tmp is None: return None
    vac_href = 'https://www.superjob.ru' + tmp.get('href')
    #print(vac_href)
    tmp = html.find('span', {'class': 'f-test-text-company-item-salary'})
    #print(tmp.text)
    vac_salary = get_salary(tmp.text) if tmp is not None else ''
    if vac_salary is None: vac_salary = ''
    tmp = html.find('span', {'class': 'f-test-text-company-item-location'})
    #print(tmp.text)
    vac_location = re.findall('[А-ЯЁ]{1}.+', tmp.text)[0] if tmp is not None else ''
    #print(vac_location)
    return get_vac_dict(vac_name, vac_location, vac_salary, vac_href)

def get_sj_vacancies(link, depth, delay=True):
    vacs = []
    for i in range(depth):
        if i == 0:
            req = requests.get(link, headers=headers)
        else:
            req = requests.get(link + '&page=' + str(i+1), headers=headers)
        if req.status_code != 200: break
        
        #with open(f'test{i}.html', 'w', encoding='utf-8') as f:
        #    f.write(req.text)

        soup = BeautifulSoup(req.text, 'html.parser')
        vac_html = soup.find_all('div', {'class': '_3zucV _2GPIV i6-sc _3VcZr'})
        if delay: sleep(randint(3, 5))
         
        for vac in vac_html:
            dct = parse_sj_vacancy(vac)
            if dct is None: continue
            vacs.append(dct)
    return vacs

hh_link = hh_link.format(vac_name, vac_location)
hh_vacs = get_hh_vacancies(hh_link, depth, False)
if not hh_vacs:
    print('Вакансий не найдено')
else:
    pass
    #pprint(hh_vacs)
    
sj_link = sj_link.format(vac_name, vac_location)
sj_vacs = get_sj_vacancies(sj_link, depth, False)
if not sj_vacs:
    print('Вакансий не найдено')
else:
    pass
    #pprint(sj_vacs)
    
client = MongoClient('mongodb://127.0.0.1:27017')
db = client['jobdb']
jobdb = db.jobdb
jobdb.delete_many({})

jobdb.insert_many(hh_vacs)
jobdb.insert_many(sj_vacs)

objects = jobdb.find({'sal': {'$gt': 100000}})
for i in objects:
    print(i)





    
