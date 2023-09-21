import requests
import pandas as pd

df_ip=pd.read_csv('domains.csv')

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

df_ip.to_csv('domains_op.csv')