import undetected_chromedriver as uc
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from config import MONGOURL,APOLLO_EMAIL,APOLLO_PASSWORD
from pymongo import MongoClient
from datetime import datetime
import time 
from tqdm import tqdm
import json

# Constants for API URLs
LOGIN_URL='https://app.apollo.io/#/login'

def login(driver):
    driver.get(LOGIN_URL)
    time.sleep(10)
    driver.find_element('xpath','//input[@name="email"]').send_keys(APOLLO_EMAIL)
    driver.find_element('xpath','//input[@name="password"]').send_keys(APOLLO_PASSWORD)
    driver.find_element('xpath','//input[@name="password"]').send_keys(Keys.ENTER)
    time.sleep(10)

client = MongoClient(MONGOURL)

db = client['companydatabase']
collection_apollo_company = db['apollo_company_api']

# Query for documents where "estimated_num_employees" is not available
query = {"estimated_num_employees": {"$exists": False}}
# Project only the "id" field
projection = {"id": 1, "_id": 0}
# Retrieve all documents and extract the "base domain" values
base_ids_mongo = [doc.get("id", None) for doc in collection_apollo_company.find(query, projection)]
base_ids_mongo=[doc for doc in base_ids_mongo if doc]
print(len(base_ids_mongo))

driver=uc.Chrome()
login(driver)
#remove popup
driver.execute_script("arguments[0].remove();", driver.find_element(By.XPATH, '//div[@role="dialog"]'))

for id in tqdm(base_ids_mongo):
    url='https://app.apollo.io/api/v1/organizations/'+id
    driver.get(url)
    time.sleep(10)
    content = driver.find_element(By.TAG_NAME,'pre').text
    parsed_json = json.loads(content)['organization']
    parsed_json['updateAt']=datetime.now()
    if parsed_json:
        collection_apollo_company.update_one({"id":id}, {'$set': parsed_json}, upsert=True)
    print(f'Crawled : {id}')