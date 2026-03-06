# ------------------------------------------------
# TELEGRAM DEAL BOT
# ------------------------------------------------
# Funktionen:
# - liest MyDealz RSS Feed
# - postet Deals automatisch in Telegram
# - postet Bilder
# - filtert Deals nach Temperatur
# - verhindert Doppelposts
# - markiert Amazon Deals
# - zeigt Debug Infos in Railway Logs
# ------------------------------------------------

import os
import asyncio
import feedparser
from telegram import Bot


# ------------------------------------------------
# KONFIGURATION
# ------------------------------------------------

TOKEN = os.getenv("TOKEN")

CHAT_ID = "@billiger_gehts_nicht"

RSS_URL = "https://www.mydealz.de/rss/deals"

MIN_TEMP = 300

posted_deals = set()


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

                import re

temp_match = re.search(r"(\d+)°", entry.title)

if temp_match:
    temperature = int(temp_match.group(1))
else:
    temperature = 0

                if temperature < MIN_TEMP:
                    continue

                valid_deals += 1

                posted_deals.add(deal_id)

                title = entry.title
                link = entry.link

                # Amazon erkennen
                is_amazon = "amazon" in link.lower()

                image = entry.get("media_content", [{}])[0].get("url", None)

                if is_amazon:
                    shop = "🛒 AMAZON DEAL"
                else:
                    shop = "🛍 DEAL"

                message = f"""
🔥 {shop} ({temperature}°)

{title}

👉 {link}
"""

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

        print("Warte 5 Minuten bis zum nächsten Check...")

        await asyncio.sleep(50)


asyncio.run(main())


