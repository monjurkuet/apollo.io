import seleniumwire.undetected_chromedriver as uc
from seleniumwire.utils import decode
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from config import MONGOURL,HOST,PORT,USERNAME,PASSWORD,APOLLO_EMAIL,APOLLO_PASSWORD
from pymongo import MongoClient
from datetime import datetime
import time 
import mysql.connector
from urllib.parse import urlparse
from tqdm import tqdm
import json

# Constants for API URLs
COMPANY_DETAILS_API = 'https://app.apollo.io/api/v1/mixed_companies/search'
LOGIN_URL='https://app.apollo.io/#/login'
COMPANY_SEARCH_URL='https://app.apollo.io/#/companies'

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

def get_domains():
    # Connect to the MySQL database
    conn = mysql.connector.connect(
        host=HOST,
        user=USERNAME,
        password=PASSWORD,
        database='apollo',
        port=PORT
        )
    # Create a cursor object to execute SQL statements
    cursor = conn.cursor()
    # Execute the SQL query to retrieve distinct values
    query = "SELECT domain FROM domains_queue WHERE status is NULL"
    cursor.execute(query)
    # Fetch all the distinct values as a list
    domains = [row[0] for row in cursor.fetchall()]
    # Close the database connection
    conn.close()
    # Print the list of distinct company LinkedIn URLs
    print(len(domains))
    return domains

# Create a reusable function for extracting real-time data
def extract_realtime_data(driver):
    details_content=None
    #Fix variables for python
    null=None
    true=True
    false=False
    for request in driver.requests:
        if request.response:
            if COMPANY_DETAILS_API in request.url and request.response.status_code == 200 :
                details_content = eval(decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity')).decode('utf-8'))
                if 'organizations' in json.dumps(details_content):
                    break
    del driver.requests
    return details_content['organizations']

client = MongoClient(MONGOURL)

db = client['companydatabase']
collection_apollo_company = db['apollo_company_api']

domains_mysql=get_domains()
# Query to retrieve all documents and project only the "base domain" field
projection = {"domain": 1, "_id": 0}
# Retrieve all documents and extract the "base domain" values
base_domains_mongo = [doc["domain"] for doc in collection_apollo_company.find({}, projection)]

new_domains= list(set(domains_mysql).symmetric_difference(set(base_domains_mongo)))
print(len(new_domains))

driver=uc.Chrome()
login(driver)
driver.get(COMPANY_SEARCH_URL)
#remove popup
if driver.find_elements(By.XPATH, '//div[@role="dialog"]'):
    driver.execute_script("arguments[0].remove();", driver.find_element(By.XPATH, '//div[@role="dialog"]'))

for domain in tqdm(new_domains):
    driver.find_element(By.XPATH,'//input[@placeholder="Search Companies..."]').clear()
    driver.find_element(By.XPATH,'//input[@placeholder="Search Companies..."]').send_keys(domain)
    driver.find_element(By.XPATH,'//input[@placeholder="Search Companies..."]').send_keys(Keys.ENTER)
    time.sleep(10)
    details_content=extract_realtime_data(driver)
    if details_content:
        details_content=details_content[0]
    else:
        details_content={}
        details_content['primary_domain']=domain
    details_content['updateAt']=datetime.now()
    if details_content['primary_domain']:
        if domain.lower() in details_content['primary_domain'].lower():
            collection_apollo_company.update_one({"domain":domain}, {'$set': details_content}, upsert=True)
    else:
        collection_apollo_company.update_one({"domain":domain}, {'$set': {}}, upsert=True)
    print(f'Crawled : {domain}')

driver.close()
driver.quit()
client.close()