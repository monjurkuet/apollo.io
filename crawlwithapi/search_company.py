import requests
from config import API_KEY,MONGOURL
import pandas as pd
from pymongo import MongoClient
from datetime import datetime
import time 

client = MongoClient(MONGOURL)

db = client['companydatabase']
collection = db['apollo_employee_api']

class ApolloAPIClient:
    def __init__(self):
        self.api_key = API_KEY
        self.base_url = "https://api.apollo.io/v1/mixed_people/search"
        self.headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json'
        }
    def search_organization_domains(self, domain):
        data = {
                "api_key": self.api_key,
                "domain": domain
            }
        response = requests.post(self.base_url, headers=self.headers, json=data)
        return response

Apolloclient = ApolloAPIClient()

person_titles=['owner','ceo','director']
person_titles=None

df_ip=pd.read_csv('domains.csv')

for i in range(0,len(df_ip)):
    domain=df_ip.loc[i,'Domain']
    response = Apolloclient.search_organization_domains(domain).json()
    people=response['people']
    df_ip.loc[i,'position']=str(person_titles)
    if not people:
        df_ip.loc[i,'available']=0
    else:
        df_ip.loc[i,'available']=1
        for each_people in people:
            each_people['updateAt']=datetime.now()
            collection.update_one({"id":each_people['id']}, {'$set': each_people}, upsert=True)
    print(domain,len(people),i)
    time.sleep(1)

df_ip.to_csv('domains_op.csv')