import requests
import pandas as pd
from urllib.parse import urlparse

df_ip=pd.read_csv('domains.csv')

# check domain
for i in range(len(df_ip)):
    domain=df_ip.loc[i,'Domain']
    print(domain)
    try:
        response=requests.get(f'https://{domain}',timeout=15)
        if response.status_code==200:
            check=1
        else:
            check=0
    except:
        check=0
    df_ip.loc[i,'check']=check
    print(df_ip.loc[i])

# normalise domain
def parse_domain(url):
    urlfinal=urlparse(url).netloc.replace("www.", "")
    if not urlfinal:
        urlfinal =urlparse(url).path.replace("www.", "")
    print(urlfinal)
    return urlfinal.lower()

for i in range(len(df_ip)):
    domain=df_ip.loc[i,'Domain']
    df_ip.loc[i,'Domain_clean']=parse_domain(domain)

df_ip.to_csv('domains_op.csv')