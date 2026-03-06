# -----------------------------
# Telegram Deal Bot
# -----------------------------
# Dieser Bot liest automatisch den RSS-Feed von MyDealz
# und postet neue Deals in einen Telegram-Kanal.
#
# Funktionen:
# - Läuft 24/7 auf Railway
# - Postet Deals mit Bild
# - Filtert Deals nach Temperatur
# - Verhindert Doppelposts
# -----------------------------

import os
import asyncio
import feedparser
from telegram import Bot


# -----------------------------
# KONFIGURATION
# -----------------------------

# Telegram Token wird aus Railway Variables geladen
TOKEN = os.getenv("TOKEN")

# Dein Telegram Kanal
CHAT_ID = "@billiger_gehts_nicht"

# RSS Feed von MyDealz
RSS_URL = "https://www.mydealz.de/rss/deals"

# Mindesttemperatur für Deals
MIN_TEMP = 300

# Liste für bereits gepostete Deals
posted_deals = set()


# -----------------------------
# HAUPTFUNKTION
# -----------------------------
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

                # -----------------------------
                # Doppelpost Schutz
                # -----------------------------

                deal_id = entry.get("id", entry.get("link"))

                if deal_id in posted_deals:
                    continue

                posted_deals.add(deal_id)

                # -----------------------------
                # Deal Temperatur prüfen
                # -----------------------------

                temperature = entry.get("temperature", 0)

                if temperature < MIN_TEMP:
                    continue

                # -----------------------------
                # Deal Informationen
                # -----------------------------

                title = entry.title
                link = entry.link

                # Bild aus RSS Feed holen
                image = entry.get("media_content", [{}])[0].get("url", None)

                # Nachricht formatieren
                message = f"""
🔥 HOT DEAL ({temperature}°)

{title}

👉 {link}
"""

                # -----------------------------
                # Nachricht senden
                # -----------------------------

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

                    # kleine Pause (Telegram Flood Schutz)
                    await asyncio.sleep(3)

                except Exception as e:
                    print("Telegram Fehler:", e)

        except Exception as e:
            print("Feed Fehler:", e)

        # -----------------------------
        # Pause bevor neuer Check
        # -----------------------------
        await asyncio.sleep(300)   # 5 Minuten


# Bot starten
asyncio.run(main())
