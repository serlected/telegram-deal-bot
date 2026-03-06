# ------------------------------------------------
# TELEGRAM DEAL BOT
# ------------------------------------------------
# Funktionen:
# - Liest MyDealz RSS Feed
# - Postet Deals automatisch in Telegram
# - Postet Dealbilder
# - Filtert Deals nach Temperatur
# - Verhindert Doppelposts
# - Markiert Amazon Deals
# - Läuft 24/7 auf Railway
# ------------------------------------------------

import os
import asyncio
import feedparser
from telegram import Bot


# ------------------------------------------------
# KONFIGURATION
# ------------------------------------------------

# Telegram Token aus Railway Variables laden
TOKEN = os.getenv("TOKEN")

# Dein Telegram Kanal
CHAT_ID = "@billiger_gehts_nicht"

# MyDealz RSS Feed
RSS_URL = "https://www.mydealz.de/rss/deals"

# Mindesttemperatur für Deals
MIN_TEMP = 300

# Set für bereits gepostete Deals
posted_deals = set()


# ------------------------------------------------
# HAUPTFUNKTION
# ------------------------------------------------

async def main():

    # Telegram Bot initialisieren
    bot = Bot(token=TOKEN)

    print("Bot gestartet...")

    # Endlosschleife (läuft dauerhaft)
    while True:

        try:
            # RSS Feed laden
            feed = feedparser.parse(RSS_URL)

            # Alle Deals im Feed durchgehen
            for entry in feed.entries:

                # ------------------------------------------------
                # Doppelpost Schutz
                # ------------------------------------------------

                deal_id = entry.get("id", entry.get("link"))

                if deal_id in posted_deals:
                    continue

                posted_deals.add(deal_id)

                # ------------------------------------------------
                # Temperatur prüfen
                # ------------------------------------------------

                temperature = entry.get("temperature", 0)

                if temperature < MIN_TEMP:
                    continue

                # ------------------------------------------------
                # Deal Informationen
                # ------------------------------------------------

                title = entry.title
                link = entry.link

                # Amazon Deal erkennen
                is_amazon = "amazon" in link.lower()

                # Deal Bild aus RSS holen
                image = entry.get("media_content", [{}])[0].get("url", None)

                # ------------------------------------------------
                # Nachricht formatieren
                # ------------------------------------------------

                if is_amazon:
                    shop = "🛒 AMAZON DEAL"
                else:
                    shop = "🛍 DEAL"

                message = f"""
🔥 {shop} ({temperature}°)

{title}

👉 {link}
"""

                # ------------------------------------------------
                # Nachricht senden
                # ------------------------------------------------

                try:

                    # Wenn Bild vorhanden → Bild posten
                    if image:
                        await bot.send_photo(
                            chat_id=CHAT_ID,
                            photo=image,
                            caption=message
                        )

                    # sonst normalen Text senden
                    else:
                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=message
                        )

                    print("Deal gepostet:", title)

                    # Pause um Telegram Flood zu vermeiden
                    await asyncio.sleep(3)

                except Exception as e:
                    print("Telegram Fehler:", e)

        except Exception as e:
            print("Feed Fehler:", e)

        # ------------------------------------------------
        # Pause bis zum nächsten RSS Check
        # ------------------------------------------------

        await asyncio.sleep(300)  # 5 Minuten


# Bot starten
asyncio.run(main())
