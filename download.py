import urllib.request
from bs4 import BeautifulSoup
from PIL import Image, ImageFile
import os
import pandas as pd
import re
import io
import base64
import time
import ssl
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import urllib.error

# Configurări generaleQ
ImageFile.LOAD_TRUNCATED_IMAGES = True
ssl_context = ssl._create_unverified_context()
max_threads = 20
save_dir = "favicons"
retry_file = "failed_downloads.txt"

# ======== Funcție de descărcare favicon ========
def download_favicon(site_url, save_dir=save_dir):
    try:
        os.makedirs(save_dir, exist_ok=True)
        headers = {'User-Agent': 'Mozilla/5.0'}
        req = urllib.request.Request(site_url, headers=headers)

        with urllib.request.urlopen(req, timeout=5, context=ssl_context) as response:
            soup = BeautifulSoup(response.read(), 'html.parser')

        icon_link = soup.find("link", rel=lambda x: x and 'icon' in x.lower())
        if icon_link and icon_link.get("href"):
            icon_url = icon_link["href"]
        else:
            icon_url = site_url.rstrip("/") + "/favicon.ico"

        if icon_url.startswith("data:"):
            data = icon_url.split(",", 1)[-1]
            image_data = base64.b64decode(data)
            content_type = "image/png"
        else:
            if icon_url.startswith("//"):
                icon_url = "https:" + icon_url
            elif icon_url.startswith("/"):
                icon_url = site_url.rstrip("/") + icon_url
            elif not icon_url.startswith("http"):
                icon_url = site_url.rstrip("/") + "/" + icon_url

            req_icon = urllib.request.Request(icon_url, headers=headers)
            with urllib.request.urlopen(req_icon, timeout=5, context=ssl_context) as response:
                content_type = response.info().get_content_type()
                image_data = response.read()

        domain_name = re.sub(r'https?://(www\.)?', '', site_url).strip('/')
        domain_name = re.sub(r'[^\w\-\.]', '_', domain_name)
        base_path = os.path.join(save_dir, domain_name)

        if os.path.exists(base_path + ".png") or os.path.exists(base_path + ".svg"):
            print(f"[{site_url}] Favicon deja descărcat.")
            return True

        if content_type == "image/svg+xml":
            with open(base_path + ".svg", "wb") as f:
                f.write(image_data)
            print(f"[{site_url}] Salvat SVG: {base_path}.svg")
            return True

        try:
            img = Image.open(io.BytesIO(image_data)).convert("RGBA")
            img.save(base_path + ".png", format="PNG")
            print(f"[{site_url}] Salvat PNG: {base_path}.png")
            return True
        except Exception as e:
            with open(base_path + ".bin", "wb") as f:
                f.write(image_data)
            print(f"[{site_url}] Salvat ca fișier brut (PIL fail): {base_path}.bin")
            return True

    except urllib.error.HTTPError as e:
        print(f"[{site_url}] HTTP Error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        print(f"[{site_url}] Network Error: {e.reason}")
    except Exception as e:
        print(f"[{site_url}] Eroare generală: {e}")

    return False

# ======== Retry și procesare alternativă ========
def retry_download(domain, retries=2):
    for _ in range(retries + 1):
        if download_favicon(domain):
            return True
        time.sleep(1)
    return False

def process_domain(domain):
    if not domain.startswith("http"):
        domain = "https://" + domain

    if retry_download(domain):
        return None

    if not domain.startswith("https://www."):
        alt_domain = "https://www." + domain.replace("https://", "")
        if retry_download(alt_domain):
            return None

    return domain

# ======== Funcție generală de descărcare dintr-o listă de domenii ========
def process_domains(domains, etapa="Inițial"):
    failed = []
    print(f"\n🔄 Etapa: {etapa} - {len(domains)} domenii de procesat.")
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(process_domain, domain) for domain in domains]
        for future in tqdm(as_completed(futures), total=len(futures), desc=f"{etapa} - Descărcare favicon-uri"):
            result = future.result()
            if result:
                failed.append(result)
    return failed

# ======== 1. Procesare inițială din fișierul Parquet ========
file_path = 'logos.snappy.parquet'
data = pd.read_parquet(file_path)
domains = data['domain'].dropna().unique().tolist()
initial_failed = process_domains(domains, etapa="Inițial")

# ======== 2. Salvare domenii eșuate ========
if initial_failed:
    with open(retry_file, "w", encoding="utf-8") as f:
        for d in initial_failed:
            f.write(d + "\n")
    print(f"\n⚠️ Domenii eșuate salvate în '{retry_file}' ({len(initial_failed)} domenii).")
else:
    print("\n✅ Toate favicon-urile au fost descărcate cu succes.")

# ======== 3. Retry automat pe domeniile eșuate ========
if os.path.exists(retry_file):
    with open(retry_file, "r", encoding="utf-8") as f:
        retry_domains = [line.strip() for line in f if line.strip()]
    
    if retry_domains:
        second_failed = process_domains(retry_domains, etapa="Retry")
        if second_failed:
            with open(retry_file, "w", encoding="utf-8") as f:
                for d in second_failed:
                    f.write(d + "\n")
            print(f"\n❌ Încă {len(second_failed)} domenii au eșuat la retry.")
        else:
            os.remove(retry_file)
            print("\n🎉 Toate favicon-urile au fost descărcate cu succes după retry!")
