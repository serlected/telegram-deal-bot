import os
import asyncio
import feedparser
import aiohttp
import requests
import re
from bs4 import BeautifulSoup
from telegram import Bot

TOKEN = os.getenv("TOKEN")
CHAT_ID = "@billiger_gehts_nicht"

MYDEALZ_RSS = "https://www.mydealz.de/rss/deals"

posted_links = set()
posted_titles = set()


# -------------------------
# PREIS ERKENNUNG
# -------------------------

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


# -------------------------
# KATEGORIE
# -------------------------

def detect_category(text):

    text = text.lower()

    if any(x in text for x in ["schuh","sneaker","running","air max","ultraboost"]):
        return "👟 SCHUHE"

    if any(x in text for x in ["hoodie","shirt","hose","shorts","jacke"]):
        return "👕 KLEIDUNG"

    if any(x in text for x in ["protein","creatin","booster"]):
        return "🥤 SUPPLEMENTS"

    if any(x in text for x in ["hantel","fitness","gym"]):
        return "🏋️ FITNESS"

    return "🏃 SPORT"


# -------------------------
# DUPLICATE FILTER
# -------------------------

def is_duplicate(title):

    short = title.lower()[:50]

    if short in posted_titles:
        return True

    posted_titles.add(short)

    return False


# -------------------------
# DEAL HINZUFÜGEN
# -------------------------

def add_deal(deals,title,link,shop,image=None):

    if link in posted_links:
        return

    if is_duplicate(title):
        return

    price,old_price,discount = extract_prices(title)

    if discount and discount < 20:
        return

    category = detect_category(title)

    deals.append({
        "title":title,
        "link":link,
        "shop":shop,
        "price":price,
        "old_price":old_price,
        "discount":discount,
        "category":category,
        "image":image
    })


# -------------------------
# MYDEALZ
# -------------------------

def get_mydealz():

    deals=[]

    feed=feedparser.parse(MYDEALZ_RSS)

    for entry in feed.entries:

        title=entry.title
        link=entry.link

        image=None

        if "media_content" in entry:
            image=entry.media_content[0]["url"]

        add_deal(deals,title,link,"MYDEALZ",image)

    return deals


# -------------------------
# GENERISCHER SCRAPER
# -------------------------

def scrape(url,selector,prefix,shop):

    deals=[]

    try:

        r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"})
        soup=BeautifulSoup(r.text,"html.parser")

        items=soup.select(selector)

        for i in items[:10]:

            title=i.get_text().strip()
            link=i.get("href")

            image=None

            img=i.find("img")

            if img:
                image=img.get("src")

            if prefix:
                link=prefix+link

            add_deal(deals,title,link,shop,image)

    except Exception as e:

        print(shop,"Fehler:",e)

    return deals


# -------------------------
# AMAZON
# -------------------------

def get_amazon():

    deals=[]

    try:

        url="https://www.amazon.de/gp/goldbox"

        r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"})
        soup=BeautifulSoup(r.text,"html.parser")

        cards=soup.select("div[data-cy='deal-card']")

        for c in cards[:10]:

            title=c.get_text().strip()

            link_tag=c.find("a")

            img=c.find("img")

            link=None
            image=None

            if link_tag:
                link="https://www.amazon.de"+link_tag.get("href")

            if img:
                image=img.get("src")

            if link:
                add_deal(deals,title,link,"AMAZON",image)

    except Exception as e:

        print("Amazon Fehler",e)

    return deals


# -------------------------
# EBAY
# -------------------------

def get_ebay():

    deals=[]

    try:

        url="https://www.ebay.de/deals"

        r=requests.get(url,headers={"User-Agent":"Mozilla/5.0"})
        soup=BeautifulSoup(r.text,"html.parser")

        items=soup.select("div.ebayui-dne-item-featured-card")

        for i in items[:10]:

            title=i.get_text().strip()

            a=i.find("a")
            img=i.find("img")

            link=None
            image=None

            if a:
                link=a.get("href")

            if img:
                image=img.get("src")

            if link:
                add_deal(deals,title,link,"EBAY",image)

    except Exception as e:

        print("Ebay Fehler",e)

    return deals


# -------------------------
# BOT
# -------------------------

async def main():

    bot=Bot(token=TOKEN)

    print("Sport Deal Bot V6 gestartet")

    while True:

        try:

            deals=[]

            deals+=get_mydealz()

            deals+=scrape("https://www.nike.com/de/w/sale-3yaep",
                          "a.product-card__link-overlay",
                          "https://www.nike.com",
                          "NIKE")

            deals+=scrape("https://www.adidas.de/sale",
                          "a.gl-product-card__assets-link",
                          "https://www.adidas.de",
                          "ADIDAS")

            deals+=scrape("https://eu.puma.com/de/de/sale",
                          "a.tile-root",
                          "",
                          "PUMA")

            deals+=scrape("https://www.decathlon.de/de/sale",
                          "a[data-testid='product-card-link']",
                          "https://www.decathlon.de",
                          "DECATHLON")

            deals+=get_amazon()
            deals+=get_ebay()


            for deal in deals:

                posted_links.add(deal["link"])

                message=f"""
⭐ {deal['shop']} TOP DEAL

{deal['category']}

{deal['title']}
"""

                if deal["price"]:

                    if deal["old_price"]:

                        message+=f"\n💰 {deal['price']} statt {deal['old_price']}"

                        if deal["discount"]:
                            message+=f"\n📉 -{deal['discount']}%"

                    else:

                        message+=f"\n💰 {deal['price']}"

                message+=f"\n\n👉 {deal['link']}"

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

                print("Deal gepostet:",deal["title"])

                await asyncio.sleep(2)

        except Exception as e:

            print("Bot Fehler:",e)

        await asyncio.sleep(180)


asyncio.run(main())
