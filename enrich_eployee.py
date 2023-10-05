import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from config import MONGOURL,APOLLO_EMAIL,APOLLO_PASSWORD
from pymongo import MongoClient
from datetime import datetime
import time 
from tqdm import tqdm
import json
import pandas as pd
from urllib.parse import urlparse

# Constants for API URLs
LOGIN_URL='https://app.apollo.io/#/login'

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

client = MongoClient(MONGOURL)
db = client['companydatabase']
collection_apollo_employee = db['apollo_employee_api']
collection_apollo_employee_emails = db['apollo_employee_emails']

input_domains=pd.read_csv('domains.csv').domain.tolist()
input_domains=[parse_domain(i) for i in input_domains]
#mongodb query
query = {"domain": {"$in": input_domains}}
projection = {"id": 1} 
mongodb_result = collection_apollo_employee.find(query, projection)
mongodb_result=[i['id'] for i in mongodb_result]

driver=uc.Chrome()
login(driver)
#remove popup
driver.execute_script("arguments[0].remove();", driver.find_element(By.XPATH, '//div[@role="dialog"]'))

for id in tqdm(mongodb_result[25:]):
    url='https://app.apollo.io/#/people/'+id
    driver.get(url)
    time.sleep(10)
    driver.find_element(By.XPATH,'//div[text()="Access Email & Phone Number"]').click()
    time.sleep(5)
    contactid=driver.current_url.rstrip('/').split('/')[-1]
    url='https://app.apollo.io/api/v1/contacts/'+contactid
    driver.get(url)
    time.sleep(2)
    content = driver.find_element(By.TAG_NAME,'pre').text
    parsed_json = json.loads(content)['contact']
    parsed_json['updateAt']=datetime.now()
    if parsed_json:
        collection_apollo_employee_emails.update_one({"person_id":id}, {'$set': parsed_json}, upsert=True)
    print(f'Crawled : {id}')