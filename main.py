# This program is scraping all the details from marketplace!!!!!!

import csv
import datetime
import re
import schedule
import time
import pyodbc
from playwright.sync_api import sync_playwright, TimeoutError
from config.settings import DB_CONFIG


# -------------------- DB CONFIG -------------------- #
# Database configuration
# server = 'tcp:192.168.100.11'
# database = 'BuyFromDB'
# username = 'hyd_scrape'
# password = 'hyd$cr@93#@@@'

connection_string = f'DRIVER={{SQL Server}};SERVER={DB_CONFIG['server']};DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']}'
connection = pyodbc.connect(connection_string)
cursor = connection.cursor()

# -------------------- DB QUERY -------------------- #
cursor.execute(""" SELECT DISTINCT SKU, BuyfromURL
                    FROM 
                    (
                        SELECT
                            bd.Asin AS SKU, bd.BuyfromURL
                        FROM LINKEDASL.OrdersDB.dbo.buyfromasindetailsdata bd
                        JOIN LINKEDASL.OrdersDB.dbo.BuyFromMainAsin bm ON bm.id=bd.BuyFromMainID
                        JOIN LINKEDASL.OrdersDB.dbo.MarketPlaceMaster mp ON mp.MarketPlaceID=bd.BuyFromId
                        JOIN PricingDB.dbo.supplychainsixtyforty rp ON rp.buyfrommainid=bd.BuyFromMainID
                        WHERE BuyFromId=379
                        AND bd.Asin NOT IN (
                           SELECT SKU FROM Tbl_ContarmarketMainScrap
                            WHERE CAST(ScrapedDate AS DATE)=CAST(GETDATE()+1 AS DATE)
                        )
                    )BB
                     """)

rows = cursor.fetchall()
# print("rows:::::", rows)

def get_connection():
    """
    Establish and return a database connection and cursor.
    """
    conn_str = (
        f"DRIVER={{SQL Server}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        f"Connection Timeout=30;"
    )
    connection = pyodbc.connect(conn_str, autocommit=True)
    cursor = connection.cursor()
    return connection, cursor

def insert_scraped_data(cursor, data):
    """
    Insert a row into the Tbl_ContarmarketMainScrap table.
    Retries if connection is lost.
    """
    query = '''
        INSERT INTO Tbl_ContarmarketMainScrap (
        SKU, Title, QntyText, Quantity, StatusText, Status, UPC, Price, MPrice, AsinPack, BuyFromUrl, ScrapedDate
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    try:
        cursor.execute(query, data)
        cursor.commit()
    except pyodbc.OperationalError:
        print("Connection lost. Reconnecting...")
        # Retry logic (could be more robust in real apps)
        connection, new_cursor = get_connection()
        new_cursor.execute(query, data)
        new_cursor.commit()



def main():
    # -------------------- SCRAPING FUNCTION -------------------- #
    def scrape_product_data_selenium(url):
        print("\nOpening:", url)
        if url=="":
            return "ProductUrlNotFound", "", 0, "", 0, "", 0, 0, 0, ""
        page.goto(url, timeout=60000)
        time.sleep(5)
        # -------- Website login popup!!!!!!!! -------- #
        try:
            page.locator("button.modal__close-btn").click(timeout=10000)
            print("Popup closed successfully.")
        except Exception as e:
            print("Popup not found:")

        # -------- Product Title -------- #
        try:
            page.wait_for_selector(".product-title.h4", timeout=10000)
            title = page.locator(".product-title.h4").inner_text().strip()
        except TimeoutError:
            title = "ProductNotFound"
            return title, "", 0, "", 0, "", 0, 0, 0, ""
        print("Product Title:", title)

        # -------- Product Price -------- #
        try:
            price_locator = page.locator("span.price__current").filter(has_text="$")
            price_text = price_locator.inner_text()
            price = price_text.replace("$", "").replace(",", "").strip()

        except Exception as e:
            print("Error occured:",e)
            price = 0.0
        print("Price:", price)

        # -------- Member price -------- #
        try:
            price_text = page.locator("span.MembersPrice").first.text_content(timeout=2000)
            match = re.search(r"\d+\.\d+", price_text)
            mprice = match.group()
        except:
            try:
                price_text = page.locator("span.cp-price-final").first.text_content(timeout=2000)
                match = re.search(r"\d+\.\d+", price_text)
                mprice = match.group()
            except Exception as e:
                print("Error occured", e)
                mprice = 0.0
        print("Member Price:", mprice)

        # -------- Product pack -------- #
        try:
            row = page.locator("div.info-row").filter(has_text="Unit Box:")
            unit_box = row.locator("div.value").inner_text().strip()
        except Exception as e:
            try:
                row = page.locator("div.info-row").filter(has_text="Units:")
                unit_box = row.locator("div.value").inner_text().strip()
            except:
                print("Error Occured", e)
                unit_box = 0
        print("Unit Box:", unit_box)

        # -------- Stock Status -------- #
        try:
            page.wait_for_selector("button[class='btn js-add-to-cart btn--primary w-full']", timeout=10000)
            statustext = page.locator("button[class='btn js-add-to-cart btn--primary w-full']").inner_text().strip()
            status = 1
            try:
                page.wait_for_selector("div[class='preorder-minimum'] p", timeout=10000)
                Qntytext = page.locator("div[class='preorder-minimum'] p").inner_text().strip()
                # extract number using regex
                if Qntytext:
                    match = re.search(r"\d+", Qntytext)
                    Qnty = match.group() if match else 99
            except TimeoutError:
                Qntytext = "QntyNotFound"
                Qnty = 99
        except TimeoutError:
            Qntytext = "QntyNotFound"
            Qnty = 0
            try:
                statustext = page.locator(".restock-rocket-button-cover").inner_text().strip()
                status = 0
            except:
                statustext = "Status Text NotFound"
                status = 0
        print("Status Text:", statustext)
        print("status:", status)

        # -------- BarCode -------- #
        try:
            page.wait_for_selector("div.info-row:has-text('UPC') div.value", timeout=10000)
            UPC = page.locator("div.info-row:has-text('UPC') div.value").inner_text().strip()
        except TimeoutError:
            UPC = "BarCodeNotFound"
        print("BarCode", UPC)

        # -------- sku -------- #
        try:
            sku = page.locator(
                "//div[div/strong[contains(text(),'SKU:')]]/div[@class='value']"
            ).text_content()
            sku = sku.strip() if sku else ""
            print("SKU:", sku)

        except Exception as e:
            sku = ""
            print("SKU not found:", e)

        return title, Qntytext, Qnty, statustext, status, UPC, price, mprice, unit_box, sku

    # -------------------- MAIN EXECUTION -------------------- #
    try:
        # Open a CSV file for writing
        with open("Test4.csv", "w", newline="", encoding="utf-8") as csv_file:
            csv_writer = csv.writer(csv_file)
            current_date = datetime.date.today() + datetime.timedelta(days=1)
            current_date = current_date.strftime("%m/%d/%Y")

            # Write headers to the CSV file
            csv_writer.writerow(
                ["Asin", "Title", "Qntytext", "Qnty", "statustext", "status", "UPC", "price", "mprice", "unit_box", "ScrapedDate", "SKU", "BuyFromURL"])

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()

                page.goto("https://www.contarmarket.com", timeout=60000)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(60)

                for row in rows:
                    Asin = row[0].strip()
                    Url = row[1].strip()
                    # Scrape product data using Selenium Function!
                    Title, Qntytext, Qnty, statustext, status, UPC, price, mprice, unit_box, SKU  = scrape_product_data_selenium(Url)

                    # Insert into database
                    insert_scraped_data(cursor, (
                        Asin, Title, Qntytext, Qnty, statustext, status, UPC, price, mprice, unit_box, Url, current_date
                    ))

                    # Write data to CSV
                    csv_writer.writerow(
                        [Asin, Title, Qntytext, Qnty, statustext, status, UPC, price, mprice, unit_box, current_date, SKU, Url])
                    csv_file.flush()

                browser.close()

    except Exception as e:
        print("Exception occurred:", e)

# Manual run !!!!!!!!!!!!!!!!!!!!!!
main()

# def job():
#     main()
# # Schedule the job to run every day at 17:30
# schedule.every().day.at("01:00").do(job)
#
# # Run the scheduler continuously
# while True:
#     print("Task started successfully!!!!!!!!!!")
#     schedule.run_pending()
#     time.sleep(1800)




