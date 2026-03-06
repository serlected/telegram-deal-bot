import os
import asyncio
import feedparser
import re
from telegram import Bot


# -------------------------------
# KONFIGURATION
# -------------------------------

TOKEN = os.getenv("TOKEN")

CHAT_ID = "@billiger_gehts_nicht"

RSS_URL = "https://www.mydealz.de/rss/deals"

MIN_TEMP = 10

posted_deals = set()


# -------------------------------
# HAUPTFUNKTION
# -------------------------------

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


                # -------------------------------
                # Temperatur erkennen
                # -------------------------------

                text_to_check = entry.title + " " + entry.get("description", "")

                temp_match = re.search(r"(\d+)\s*°", text_to_check)

                if temp_match:
                    temperature = int(temp_match.group(1))
                else:
                    temperature = 0

                print("Temperatur erkannt:", temperature)

                if temperature < MIN_TEMP:
                    continue

                valid_deals += 1
                posted_deals.add(deal_id)


                # -------------------------------
                # Deal Infos
                # -------------------------------

                title = entry.title
                link = entry.link
                description = entry.get("description", "")


                # -------------------------------
                # echten Shop Link finden
                # -------------------------------

                urls = re.findall(r'https?://[^\s"]+', description)

                real_link = link

                for url in urls:
                    if "static.mydealz" not in url:
                        real_link = url
                        break


                # -------------------------------
                # Shop erkennen
                # -------------------------------

                link_lower = real_link.lower()

                if "amazon" in link_lower:
                    shop = "🛒 AMAZON"
                elif "mediamarkt" in link_lower:
                    shop = "🛒 MEDIAMARKT"
                elif "saturn" in link_lower:
                    shop = "🛒 SATURN"
                elif "otto" in link_lower:
                    shop = "🛒 OTTO"
                elif "ebay" in link_lower:
                    shop = "🛒 EBAY"
                else:
                    shop = "🛍 DEAL"


                # -------------------------------
                # Bild holen
                # -------------------------------

                image = entry.get("media_content", [{}])[0].get("url", None)


                # -------------------------------
                # Nachricht bauen
                # -------------------------------

                message = f"""
🔥 {shop} ({temperature}°)

{title}

👉 {real_link}
"""


                # -------------------------------
                # Nachricht senden
                # -------------------------------

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

        print("Warte bis zum nächsten Check...")

        await asyncio.sleep(50)


asyncio.run(main())
