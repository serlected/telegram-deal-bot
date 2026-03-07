import os
import asyncio
import requests
from telegram import Bot


TOKEN = os.getenv("TOKEN")
CHAT_ID = "@billiger_gehts_nicht"

posted_links = set()


# ---------------------------------
# AMAZON DEAL API
# ---------------------------------

def get_amazon_deals():

    deals = []

    url = "https://www.amazon.de/gp/goldbox?nocache=1"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:

        r = requests.get(url, headers=headers)

        text = r.text

        lines = text.split('"dealID"')

        for line in lines[1:20]:

            try:

                title = line.split('"title":"')[1].split('"')[0]

                link = "https://www.amazon.de/gp/goldbox"

                image = None

                deals.append({
                    "title": title,
                    "link": link,
                    "image": image
                })

            except:
                pass

    except Exception as e:

        print("Amazon Fehler:", e)

    return deals


# ---------------------------------
# BOT
# ---------------------------------

async def main():

    bot = Bot(token=TOKEN)

    print("Amazon Deal Bot V2 gestartet")

    while True:

        try:

            deals = get_amazon_deals()

            print("Gefundene Deals:", len(deals))

            for deal in deals:

                if deal["title"] in posted_links:
                    continue

                posted_links.add(deal["title"])

                message = f"""
🛒 AMAZON DEAL

{deal['title']}

👉 {deal['link']}
"""

                try:

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
