# DB settings
DB_CONFIG = {
    'server' : 'tcp:192.168.100.11',
    'database' : 'BuyFromDB',
    'username' : 'hyd_scrape',
    'password' : 'hyd$cr@93#@@@'
}


try:
    sku = None

    scripts = page.locator("script").all()

    for script in scripts:
        text = script.inner_text()

        if '"sku"' in text:
            match = re.search(r'"sku"\s*:\s*"([^"]+)"', text)

            if match:
                sku = match.group(1)
                break

    print("SKU:", sku)

except Exception as e:
    print("SKU not found:", e)
    sku = None
