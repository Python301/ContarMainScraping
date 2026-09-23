# DB settings
DB_CONFIG = {
    'server' : 'tcp:192.168.100.11',
    'database' : 'BuyFromDB',
    'username' : 'hyd_scrape',
    'password' : 'hyd$cr@93#@@@'
}



try:
    price_text = page.locator("span.cp-mw__final").first.text_content(timeout=2000)
    match = re.search(r"\d+\.\d+", price_text)

    if match:
        mprice = match.group()
    else:
        mprice = 0.0

except Exception:
    try:
        price_text = page.locator("span.MembersPrice").first.text_content(timeout=2000)
        match = re.search(r"\d+\.\d+", price_text)

        if match:
            mprice = match.group()
        else:
            mprice = 0.0

    except Exception as e:
        print("Error occurred:", e)
        mprice = 0.0

print("Member Price:", mprice)
