import os
import requests
import re
import csv
import time
from datetime import datetime, timedelta

today_date_str = datetime.now().strftime('%Y/%m/%d')
url = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList/v2"

headers = {
    "Host": "jlcpcb.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-GB,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Content-Type": "application/json",
    "Origin": "https://jlcpcb.com",
    "DNT": "1",
    "Connection": "keep-alive",
    "Referer": "https://jlcpcb.com/parts/basic_parts",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=0",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

def update_component(components, lcsc_code):
    for component in components:
        if component['lcsc'] == lcsc_code:
            component['Last Seen'] = today_date_str
            return False

    # Component doesn't exist, add it
    new_component = {
        'lcsc': lcsc_code,
        'First Seen': today_date_str,
        'Last Seen': today_date_str
    }
    components.append(new_component)
    return True

file_location  = os.path.join("scraped", "ComponentList.csv")

with open(file_location, "r", newline="") as f:
    reader = csv.DictReader(f)
    components = list(reader)
    # print(list(reader))
    # for row in reader:
    #     component_codes.append(row["lcsc"])

empty_page = False
page = 1
total_unseen_components = 0

while empty_page == False:
    request_json = {
        "currentPage": page,
        "pageSize": 100,
        "keyword": None,
        "componentLibraryType": "base",
        "preferredComponentFlag": True,
        "stockFlag": None,
        "stockSort": None,
        "firstSortName": None,
        "secondSortName": None,
        "componentBrand": None,
        "componentSpecification": None,
        "componentAttributes": [],
        "searchSource": "search",
    }

    response = requests.post(url, headers=headers, json=request_json)
    print(f"Page {page}: {response.status_code} {response.headers}")    
    unseen_components = 0

    if response.status_code == 200:
        page_components = re.findall(r'"componentCode":"C(\d+)"', response.text)
        for component in page_components:
            lcsc_code = component
            if update_component(components, lcsc_code):
                unseen_components+=1
                total_unseen_components+=1

    print(f"\tFound {len(page_components)} Components, {unseen_components} Unseen Components")
    if len(page_components) < 1:
        empty_page = True
    page +=1
    
    time.sleep(3)  # Pause (try to not get rate limited)

todays_date = datetime.now()
cutoff_date = todays_date - timedelta(days=14) #Components not seen in 14 days are removed from the list

components = [
    c for c in components 
    if (datetime.strptime(c['Last Seen'], '%Y/%m/%d') >= cutoff_date)
]

with open(file_location, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=components[0].keys())
    writer.writeheader()