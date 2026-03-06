# ------------------------------------------------
# TELEGRAM DEAL BOT
# ------------------------------------------------
# Funktionen
# - liest MyDealz RSS Feed
# - filtert Deals nach Temperatur
# - verhindert Doppelposts
# - lädt Deal Seite
# - findet echten Shop Link
# - erkennt Shop (Amazon / eBay etc.)
# - postet Bild + Deal in Telegram
# - zeigt Logs in Railway
# ------------------------------------------------

import os
import asyncio
import feedparser
import re
import requests
from bs4 import BeautifulSoup
from telegram import Bot


# ------------------------------------------------
# KONFIGURATION
# ------------------------------------------------

TOKEN = os.getenv("TOKEN")

CHAT_ID = "@billiger_gehts_nicht"

RSS_URL = "https://www.mydealz.de/rss/deals"

MIN_TEMP = 10

posted_deals = set()


# ------------------------------------------------
# ECHTEN SHOP LINK FINDEN
# ------------------------------------------------

def get_real_link(mydealz_link):

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(mydealz_link, headers=headers, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        links = soup.find_all("a", href=True)

        for a in links:

            url = a["href"]

            # interne Pepper Seiten ignorieren
            if any(x in url for x in [
                "mydealz",
                "pepper",
                "dealabs",
                "hotukdeals"
            ]):
                continue

            if url.startswith("http"):
                return url

    except Exception as e:

        print("Deal-Seite Fehler:", e)

    return mydealz_link


# ------------------------------------------------
# SHOP ERKENNUNG
# ------------------------------------------------

def detect_shop(link):

    link = link.lower()

    if "amazon" in link:
        return "🛒 AMAZON DEAL"

    elif "ebay" in link:
        return "🛒 EBAY DEAL"

    elif "otto" in link:
        return "🛒 OTTO DEAL"

    elif "mediamarkt" in link:
        return "🛒 MEDIAMARKT DEAL"

    elif "saturn" in link:
        return "🛒 SATURN DEAL"

    elif "alternate" in link:
        return "🛒 ALTERNATE DEAL"

    else:
        return "🛍 DEAL"


# ------------------------------------------------
# HAUPTFUNKTION
# ------------------------------------------------

async def main():

    bot = Bot(token=TOKEN)

    print("Bot gestartet...")

    while True:

        try:

            print("-----")
            print("RSS wird geprüft...")

            feed = feedparser.parse(RSS_URL)

            total_deals = len(feed.entries)
            valid_deals = 0

            print("Deals im Feed:", total_deals)

            for entry in feed.entries:

                deal_id = entry.get("id", entry.get("link"))

                if deal_id in posted_deals:
                    continue


                # ------------------------------------------------
                # Temperatur erkennen
                # ------------------------------------------------

                text_to_check = entry.title + " " + entry.get("description", "")

                temp_match = re.search(r"(\d+)\s*°", text_to_check)

                if temp_match:
                    temperature = int(temp_match.group(1))
                else:
                    temperature = 0


                if temperature < MIN_TEMP:
                    continue

                valid_deals += 1

                posted_deals.add(deal_id)


                # ------------------------------------------------
                # Deal Infos
                # ------------------------------------------------

                title = entry.title

                mydealz_link = entry.link

                real_link = get_real_link(mydealz_link)

                shop = detect_shop(real_link)

                image = entry.get("media_content", [{}])[0].get("url", None)


                # ------------------------------------------------
                # Nachricht bauen
                # ------------------------------------------------

                message = f"""
🔥 {shop} ({temperature}°)

{title}

👉 {real_link}
"""


                # ------------------------------------------------
                # Nachricht senden
                # ------------------------------------------------

                try:

                    if image:

                        await bot.send_photo(
                            chat_id=CHAT_ID,
                            photo=image,
                            caption=message
                        )

                    else:

                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=message
                        )

                    print("Deal gepostet:", title)

                    await asyncio.sleep(3)

                except Exception as e:

                    print("Telegram Fehler:", e)

            print("Deals über Temperatur:", valid_deals)

        except Exception as e:

            print("Feed Fehler:", e)

        print("Warte 60 Sekunden bis zum nächsten Check...")

        await asyncio.sleep(60)


asyncio.run(main())
