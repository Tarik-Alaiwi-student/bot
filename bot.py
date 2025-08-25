import asyncio
from playwright.async_api import async_playwright
import schedule
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import time

# Wczytaj dane logowania
load_dotenv()
EMAIL = os.getenv("EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
RECIPIENT = os.getenv("RECIPIENT")
RECIPIENT2 = os.getenv("RECIPIENT2")

EUR_TO_PLN = 4.3

DATE_LINKS = {
    "06.09.2025": 1,  # link 2
    "10.09.2025": 0,  # link 1
    "13.09.2025": 2   # link 3
}

LINKS = [
    "https://www.ryanair.com/pl/pl/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2025-09-10&originIata=CTA&destinationIata=WMI",
    "https://www.ryanair.com/pl/pl/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2025-09-06&originIata=CTA&destinationIata=WMI",
    "https://www.ryanair.com/pl/pl/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2025-09-13&originIata=CTA&destinationIata=WMI"
]

async def get_prices():
    prices = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for url in LINKS:
            await page.goto(url)
            await page.wait_for_selector("flights-price-simple.flight-card-summary__full-price", timeout=10000)
            price_text = await page.inner_text("flights-price-simple.flight-card-summary__full-price")
            eur_price = float(price_text.replace("€", "").replace(",", ".").strip())
            pln_price = round(eur_price * EUR_TO_PLN, 2)
            prices.append((pln_price, eur_price))

        await browser.close()
    return prices

def send_email(prices):
    html_lines = []
    for date_str, link_idx in DATE_LINKS.items():
        pln_price, eur_price = prices[link_idx]
        if pln_price < 425:
            price_html = f"<span style='color:red'>{pln_price} zł</span> ---> {eur_price} €"
        else:
            price_html = f"<span style='color:black'>{pln_price} zł</span>"
        html_lines.append(f"{date_str}: {price_html}")

    html_body = "<br>".join(html_lines)

    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = "Aktualne ceny lotów Ryanair"
    msg["From"] = EMAIL
    msg["To"] = RECIPIENT

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, EMAIL_PASSWORD)
        server.sendmail(EMAIL, [RECIPIENT], msg.as_string())

def job():
    prices = asyncio.run(get_prices())
    send_email(prices)
    print("Wysłano raport:", prices)

# Harmonogram
#schedule.every().day.at("04:00").do(job)
#schedule.every().day.at("08:00").do(job)
#schedule.every().day.at("14:00").do(job)
#schedule.every().day.at("16:00").do(job)
#schedule.every().day.at("18:00").do(job)
schedule.every().day.at("21:30").do(job)


print("Bot uruchomiony...")
while True:
    schedule.run_pending()
    time.sleep(1)



