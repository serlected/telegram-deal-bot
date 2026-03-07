import os
import asyncio
import requests
import re
from bs4 import BeautifulSoup
from telegram import Bot


TOKEN = os.getenv("TOKEN")
CHAT_ID = "@billiger_gehts_nicht"


posted_links = set()
posted_titles = set()


# ------------------------
# PREIS ERKENNEN
# ------------------------

def extract_prices(text):

    prices = re.findall(r"\d+[.,]?\d*\s?€", text)

    if len(prices) >= 2:

        new_price = prices[0]
        old_price = prices[1]

        try:

            n = float(new_price.replace("€","").replace(",","."))
            o = float(old_price.replace("€","").replace(",","."))
            discount = round((1 - n/o) * 100)
        except:
            discount = None

        return new_price, old_price, discount

    if len(prices) == 1:
        return prices[0], None, None

    return None, None, None


# ------------------------
# KATEGORIE ERKENNEN
# ------------------------

def detect_category(text):

    text = text.lower()

    if any(x in text for x in ["schuh","sneaker","running","air max"]):
        return "👟 SCHUHE"

    if any(x in text for x in ["shirt","jacke","hoodie","hose"]):
        return "👕 KLEIDUNG"

    if any(x in text for x in ["protein","creatin","booster"]):
        return "🥤 SUPPLEMENTS"

    if any(x in text for x in ["hantel","fitness","gym"]):
        return "🏋️ FITNESS"

    return "🛒 PRODUKT"


# ------------------------
# SPAM FILTER
# ------------------------

def is_duplicate(title):

    short = title.lower()[:60]

    if short in posted_titles:
        return True

    posted_titles.add(short)

    return False


# ------------------------
# AMAZON DEALS
# ------------------------

def get_amazon_deals():

    deals = []

    url = "https://www.amazon.de/gp/goldbox"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        r = requests.get(url, headers=headers)

        soup = BeautifulSoup(r.text, "html.parser")

        cards = soup.select("div[data-cy='deal-card']")

        for c in cards[:20]:

            title = c.get_text().strip()

            if is_duplicate(title):
                continue

            link_tag = c.find("a")

            img_tag = c.find("img")

            link = None
            image = None

            if link_tag:
                link = "https://www.amazon.de" + link_tag.get("href")

            if img_tag:
                image = img_tag.get("src")

            if not link:
                continue

            if link in posted_links:
                continue

            price, old_price, discount = extract_prices(title)

            category = detect_category(title)

            deals.append({
                "title": title,
                "link": link,
                "image": image,
                "price": price,
                "old_price": old_price,
                "discount": discount,
                "category": category
            })

    except Exception as e:

        print("Amazon Fehler:", e)

    return deals


# ------------------------
# BOT
# ------------------------

async def main():

    bot = Bot(token=TOKEN)

    print("Amazon Deal Bot V2 gestartet")

    while True:

        try:

            deals = get_amazon_deals()

            print("Gefundene Deals:", len(deals))

            for deal in deals:

                posted_links.add(deal["link"])

                message = f"""
⭐ AMAZON DEAL

{deal['category']}

{deal['title']}
"""

                if deal["price"]:

                    if deal["old_price"]:

                        message += f"\n💰 {deal['price']} statt {deal['old_price']}"

                        if deal["discount"]:
                            message += f"\n📉 -{deal['discount']}%"

                    else:

                        message += f"\n💰 {deal['price']}"

                message += f"\n\n👉 {deal['link']}"

                try:

                    if deal["image"]:

                        await bot.send_photo(
                            chat_id=CHAT_ID,
                            photo=deal["image"],
                            caption=message
                        )

                    else:

                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=message
                        )

                except Exception as e:

                    print("Telegram Fehler:", e)

                print("Deal gepostet:", deal["title"])

                await asyncio.sleep(2)

        except Exception as e:

            print("Bot Fehler:", e)

        print("Warte 3 Minuten...")

        await asyncio.sleep(180)


asyncio.run(main())
