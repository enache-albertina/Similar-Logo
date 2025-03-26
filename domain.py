import pandas as pd

# Încarcă fișierul Parquet
file_path = 'logos.snappy.parquet'  
data = pd.read_parquet(file_path)


# Extrage domeniile din coloana 'domain'
domains = data['domain'].tolist()

domains_df = pd.DataFrame(domains, columns= ['domain']);
domains_df.to_csv('domain_list.csv', index = False);

