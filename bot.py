# ------------------------------------------------
# TELEGRAM DEAL BOT
# ------------------------------------------------
# Funktionen
# - liest MyDealz RSS Feed
# - filtert Deals nach Temperatur
# - verhindert Doppelposts
# - erkennt Shop aus Titel
# - postet Bild + Deal
# - zeigt Logs in Railway
# ------------------------------------------------

import os
import asyncio
import feedparser
import re
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
# SHOP ERKENNUNG
# ------------------------------------------------

def detect_shop(text):

    text = text.lower()

    if "amazon" in text:
        return "🛒 AMAZON DEAL"

    elif "ebay" in text:
        return "🛒 EBAY DEAL"

    elif "otto" in text:
        return "🛒 OTTO DEAL"

    elif "mediamarkt" in text:
        return "🛒 MEDIAMARKT DEAL"

    elif "saturn" in text:
        return "🛒 SATURN DEAL"

    elif "alternate" in text:
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

            print("Deals im Feed:", len(feed.entries))

            valid_deals = 0

            for entry in feed.entries:

                deal_id = entry.get("id", entry.get("link"))

                if deal_id in posted_deals:
                    continue


                # ------------------------------------------------
                # Temperatur erkennen
                # ------------------------------------------------

                text = entry.title + " " + entry.get("description", "")

                temp_match = re.search(r"(\d+)\s*°", text)

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
                link = entry.link

                shop = detect_shop(title)

                image = entry.get("media_content", [{}])[0].get("url", None)


                # ------------------------------------------------
                # Nachricht bauen
                # ------------------------------------------------

                message = f"""
🔥 {shop} ({temperature}°)

{title}

👉 {link}
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
