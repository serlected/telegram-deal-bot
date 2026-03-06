import os
import asyncio
import feedparser
import re
import requests
from bs4 import BeautifulSoup
from telegram import Bot

TOKEN = os.getenv("TOKEN")

CHAT_ID = "@billiger_gehts_nicht"

RSS_URL = "https://www.mydealz.de/rss/deals"

MIN_TEMP = 10

posted_deals = set()


def get_real_link(mydealz_link):

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(mydealz_link, headers=headers, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        # mögliche Button Klassen bei MyDealz
        selectors = [
            ".cept-dealBtn",
            ".threadDealButton",
            ".thread-link",
            "a[data-type='deal']"
        ]

        for selector in selectors:

            button = soup.select_one(selector)

            if button and button.get("href"):
                return button["href"]

    except Exception as e:

        print("Fehler beim Laden der Deal-Seite:", e)

    return mydealz_link


async def main():

    bot = Bot(token=TOKEN)

    print("Bot gestartet...")

    while True:

        try:

            print("RSS wird geprüft...")

            feed = feedparser.parse(RSS_URL)

            for entry in feed.entries:

                deal_id = entry.get("id", entry.get("link"))

                if deal_id in posted_deals:
                    continue


                text = entry.title + " " + entry.get("description", "")

                temp_match = re.search(r"(\d+)\s*°", text)

                if temp_match:
                    temperature = int(temp_match.group(1))
                else:
                    temperature = 0

                if temperature < MIN_TEMP:
                    continue


                posted_deals.add(deal_id)

                title = entry.title

                mydealz_link = entry.link

                real_link = get_real_link(mydealz_link)


                link_lower = real_link.lower()

                if "amazon" in link_lower:
                    shop = "🛒 AMAZON"
                elif "ebay" in link_lower:
                    shop = "🛒 EBAY"
                elif "otto" in link_lower:
                    shop = "🛒 OTTO"
                elif "mediamarkt" in link_lower:
                    shop = "🛒 MEDIAMARKT"
                elif "saturn" in link_lower:
                    shop = "🛒 SATURN"
                else:
                    shop = "🛍 DEAL"


                image = entry.get("media_content", [{}])[0].get("url", None)


                message = f"""
🔥 {shop} ({temperature}°)

{title}

👉 {real_link}
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

        except Exception as e:

            print("Feed Fehler:", e)

        await asyncio.sleep(60)


asyncio.run(main())
