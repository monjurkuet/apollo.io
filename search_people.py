import seleniumwire.undetected_chromedriver as uc
from seleniumwire.utils import decode
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from config import MONGOURL,APOLLO_EMAIL,APOLLO_PASSWORD
from pymongo import MongoClient
from datetime import datetime
import time 
from urllib.parse import urlparse
from tqdm import tqdm
import json
import pandas as pd

# Constants for API URLs
PEOPE_SEARCH_API = 'https://app.apollo.io/api/v1/mixed_people/search'
LOGIN_URL='https://app.apollo.io/#/login'
PEOPLE_SEARCH_URL='https://app.apollo.io/#/people'
PERSONA_URL='?qPersonPersonaIds[]=651d5c5c32cfc500a3a07707' #hr,sales,operations
PERSONA_URL='?qPersonPersonaIds[]=6502e6fc0f2c8400b659ce4c' # owner level
EMAIL_FILTER='&contactEmailStatus[]=verified'

def parse_domain(url):
    urlfinal=urlparse(url).netloc.replace("www.", "")
    if not urlfinal:
        urlfinal =urlparse(url).path.replace("www.", "")
    print(urlfinal)
    return urlfinal.lower()

def login(driver):
    driver.get(LOGIN_URL)
    time.sleep(10)
    driver.find_element('xpath','//input[@name="email"]').send_keys(APOLLO_EMAIL)
    driver.find_element('xpath','//input[@name="password"]').send_keys(APOLLO_PASSWORD)
    driver.find_element('xpath','//input[@name="password"]').send_keys(Keys.ENTER)
    time.sleep(10)

def extract_realtime_data(driver):
    details_content=None
    #Fix variables for python
    null=None
    true=True
    false=False
    final_list=[]
    if driver.requests:
        for request in driver.requests:
            if request.response:
                if PEOPE_SEARCH_API in request.url and request.response.status_code == 200 :
                    details_content = eval(decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity')).decode('utf-8'))
                    if 'people' in json.dumps(details_content):
                        break
        if details_content:
            for each_people in details_content['people']+details_content['contacts']:
                final_list.append(each_people)
        del driver.requests
    return final_list

client = MongoClient(MONGOURL)
db = client['companydatabase']
collection_apollo_employee = db['apollo_employee_api']

input_domains=pd.read_csv('domains.csv').domain.tolist()

driver=uc.Chrome()
login(driver)
driver.get(PEOPLE_SEARCH_URL+PERSONA_URL+EMAIL_FILTER)
#remove popup
driver.execute_script("arguments[0].remove();", driver.find_element(By.XPATH, '//div[@role="dialog"]'))
del driver.requests

for domain in tqdm(input_domains):
    domain=parse_domain(domain)
    driver.find_element(By.XPATH,'//input[@placeholder="Search People..."]').clear()
    driver.find_element(By.XPATH,'//input[@placeholder="Search People..."]').send_keys(domain)
    driver.find_element(By.XPATH,'//input[@placeholder="Search People..."]').send_keys(Keys.ENTER)
    time.sleep(10)
    PAGINATION=0
    while PAGINATION<4:
        details_content=extract_realtime_data(driver)
        if details_content:
            for each_people in details_content:
                each_people['updateAt']=datetime.now()
                each_people['domain']=domain
                collection_apollo_employee.update_one({"id":each_people['id']}, {'$set': each_people}, upsert=True)
        print(f'Crawled : {domain}')
        if not driver.find_elements(By.XPATH,'//button[@aria-label="right-arrow"]'):
            break
        if not driver.find_element(By.XPATH,'//button[@aria-label="right-arrow"]').is_enabled():
            break
        driver.find_element(By.XPATH,'//button[@aria-label="right-arrow"]').click()
        time.sleep(10)
        PAGINATION+=1
    
driver.close()
driver.quit()
client.close()