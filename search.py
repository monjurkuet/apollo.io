import requests
from config import API_KEY

class ApolloAPIClient:
    def __init__(self):
        self.api_key = API_KEY
        self.base_url = "https://api.apollo.io/v1/mixed_people/search"
        self.headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/json'
        }
    def search_organization_domains(self, organization_domain):
        data = {
            "api_key": self.api_key,
            "q_organization_domains": organization_domain
        }
        response = requests.post(self.base_url, headers=self.headers, json=data)
        return response

client = ApolloAPIClient()
response = client.search_organization_domains("http://www.smsgoc.com")