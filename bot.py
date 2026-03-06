


import asyncio
import feedparser
import re
from telegram import Bot

import os
TOKEN = os.getenv("TOKEN")
CHAT_ID = "@billiger_gehts_nicht"

RSS_URL = "https://www.mydealz.de/rss/deals"

MIN_TEMP = 200

posted_links = set()

async def main():
    bot = Bot(token=TOKEN)

    print("Bot gestartet...")

    while True:
        try:
            feed = feedparser.parse(RSS_URL)

            for entry in feed.entries:

                if entry.link in posted_links:
                    continue

                title = entry.title

                temp_match = re.search(r'(\d+)°', title)

                if temp_match:
                    temperature = int(temp_match.group(1))
                else:
                    temperature = 0

                if temperature < MIN_TEMP:
                    continue

                posted_links.add(entry.link)

                link = entry.link

                image = None
                if "media_content" in entry:
                    image = entry.media_content[0]["url"]

                message = f"""
🔥 HOT DEAL ({temperature}°)

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

                    print("HOT Deal gepostet:", title)

                    await asyncio.sleep(3)

                except Exception as e:
                    print("Telegram Fehler:", e)

        except Exception as e:
            print("Feed Fehler:", e)

        await asyncio.sleep(60)


asyncio.run(main())
