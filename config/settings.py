# DB settings
DB_CONFIG = {
    'server' : 'tcp:192.168.100.11',
    'database' : 'BuyFromDB',
    'username' : 'hyd_scrape',
    'password' : 'hyd$cr@93#@@@'
}




import re
from selenium.webdriver.common.by import By

sku = None

try:
    scripts = driver.find_elements(By.TAG_NAME, "script")

    for script in scripts:
        text = script.get_attribute("innerHTML")

        if '"sku"' in text:
            match = re.search(r'"sku"\s*:\s*"([^"]+)"', text)

            if match:
                sku = match.group(1)
                break

    print("SKU:", sku)

except Exception as e:
    print("Error while scraping SKU:", e)
    sku = None
