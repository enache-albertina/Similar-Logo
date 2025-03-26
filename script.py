import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
import time
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Încarcă fișierul Parquet pentru a obține lista de domenii
file_path = 'logos.snappy.parquet'  # Calea către fișierul tău
data = pd.read_parquet(file_path)

# Extrage domeniile din coloana 'domain'
domains = data['domain'].tolist()
print(f"Număr domenii extrase: {len(domains)}")

# Crează un folder pentru a salva logo-urile
if not os.path.exists('logos'):
    os.makedirs('logos')

# Funcție pentru a curăța domeniul
def sanitize_domain(domain):
    return re.sub(r'[^a-zA-Z0-9.-]', '', domain)

# Funcție pentru a descărca logo-ul cu retry logic
def download_logo(domain, retries=3, delay=5, timeout=10):
    domain = sanitize_domain(domain)  # Curăță domeniul
    try:
        site_url = f"http://{domain}"
        print(f"Încerc să descarc logo-ul pentru: {domain}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': site_url
        }

        # Trimite o cerere HTTP pentru a obține conținutul paginii cu timeout
        response = requests.get(site_url, headers=headers, timeout=timeout)
        print(f"Status code pentru {site_url}: {response.status_code}")
        response.raise_for_status()  # Verifică dacă cererea a avut succes
        
        # Creează un obiect BeautifulSoup pentru a analiza HTML-ul paginii
        soup = BeautifulSoup(response.text, 'html.parser')

        # Căutăm un tag <link rel="icon"> sau <img> cu clasa "logo"
        icon_link = soup.find("link", rel="icon")
        if icon_link and icon_link.get("href"):
            logo_url = icon_link.get("href")
        else:
            img_tag = soup.find("img", class_="logo")  # Clasa "logo" poate varia
            if not img_tag:
                img_tag = soup.find("img", id="logo")  # Căutare și după id
            if img_tag and img_tag.get("src"):
                logo_url = img_tag.get("src")
            else:
                raise Exception(f"Niciun logo găsit pentru {domain}")

        # Verifică dacă URL-ul logo-ului este absolut sau relativ
        if not logo_url.startswith('http'):
            if logo_url.startswith('//'):
                logo_url = 'https:' + logo_url  # Modifică pentru a adăuga https://
            else:
                logo_url = site_url + logo_url  # Altfel, concatenăm cu site-ul principal
        
        # Descarcă imaginea logo-ului
        logo_response = requests.get(logo_url, headers=headers, verify=False, timeout=timeout)  # Bypass SSL error if needed
        logo_response.raise_for_status()
        
        # Salvează imaginea în directorul "logos"
        logo_path = f"logos/{domain}_logo.png"
        with open(logo_path, 'wb') as f:
            f.write(logo_response.content)
        
        # Success message
        print(f"Logo-ul pentru {domain} a fost descărcat cu succes!")

    except requests.exceptions.RequestException as e:
        # Error message
        print(f"Eroare la descărcarea logo-ului pentru {domain}: {e}")

        # Încearcă din nou dacă există retry-uri disponibile
        if retries > 0:
            print(f"Se va încerca din nou în {delay} secunde...")
            time.sleep(delay)
            download_logo(domain, retries - 1, delay)

# Compară toate domeniile
for domain in domains:
    download_logo(domain)
