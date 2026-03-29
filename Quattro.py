# -*- coding: utf-8 -*-
"""
Skrypt sprawdza pierwszą stronę wyszukiwania Copart.de,
wysyła na Telegram tylko nowe aukcje (te, których ID nie ma w pliku Dla_mnie.txt)
i dopisuje nowe ID do pliku.
Działa bez paginacji – tylko pierwsza strona (20 aukcji).
"""

import os
import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re

# ────────────────────────────────────────────────
# KONFIGURACJA
# ────────────────────────────────────────────────

KNOWN_IDS_FILE = "Quattro.txt"

SEARCH_URL = (
    "https://www.copart.de/en/vehicleFinderSearch?"
    "displayStr=Category:SALVAGE&"
    "from=%2FvehicleFinder&"
    "fromSource=widget&"
    "searchCriteria=%7B"
        "%22query%22:%5B%22*%22%5D,"
        "%22filter%22:%7B"
            "%22MISC%22:%5B%22-damage_type_code:(MN%20OR%20NW)%22%5D,"
            "%22MAKE%22:%5B"
                "%22lot_make_desc:%5C%22Audi%5C%22%22"
            "%5D,"
            "%22TNM%22:%5B%22transmission_type_desc:%5C%22Automatic%5C%22%22%5D,"
            "%22VFG%22:%5B%22vat_flag:%5C%22false%5C%22%22%5D,"
            "%22DRIV%22:%5B%22drive:%5C%22AWD%5C%22%22%5D,"
            "%22YEAR%22:%5B%22lot_year:%5B1920%20TO%202013%5D%22%5D,"
            "%22ODM%22:%5B%22odometer_reading_received:%5B0%20TO%20195200%5D%22%5D"
        "%7D,"
        "%22searchName%22:%22%22,"
        "%22watchListOnly%22:false,"
        "%22freeFormSearch%22:false"
    "%7D"
)

# Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")   # dodaj w GitHub Secrets
TELEGRAM_CHAT_ID   = os.getenv("TELEGRAM_CHAT_ID")     # dodaj w GitHub Secrets

# ────────────────────────────────────────────────

def send_telegram_message(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Brak TELEGRAM_TOKEN lub TELEGRAM_CHAT_ID – pomijam wysyłkę")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, data=payload, timeout=10)
        if r.status_code == 200:
            print("Wiadomość wysłana na Telegram")
        else:
            print(f"Błąd wysyłki Telegram: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Błąd wysyłki Telegram: {e}")

def load_known_ids():
    if not os.path.exists(KNOWN_IDS_FILE):
        return set()
    with open(KNOWN_IDS_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def append_new_ids(new_ids):
    if not new_ids:
        return
    with open(KNOWN_IDS_FILE, "a", encoding="utf-8") as f:
        for id_ in sorted(new_ids):
            f.write(f"{id_}\n")
    print(f"Dopisano {len(new_ids)} nowych ID do {KNOWN_IDS_FILE}")

def get_current_lot_data():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36")

    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    try:
        print("Pobieram stronę...")
        driver.get(SEARCH_URL)

        WebDriverWait(driver, 45).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/lot/"]'))
        )
        time.sleep(random.uniform(3.5, 6.0))

        soup = BeautifulSoup(driver.page_source, "html.parser")
        lot_links = soup.find_all("a", href=re.compile(r"/lot/\d+"))

        id_to_link = {}
        for link in lot_links:
            href = link.get("href", "")
            match = re.search(r"/lot/(\d+)", href)
            if match:
                lot_id = match.group(1)
                if lot_id.isdigit() and 6 <= len(lot_id) <= 9:
                    full_url = "https://www.copart.de" + href if href.startswith("/") else href
                    id_to_link[lot_id] = full_url

        print(f"Znaleziono {len(id_to_link)} aukcji na pierwszej stronie")
        return id_to_link

    except Exception as e:
        print(f"Błąd pobierania strony: {type(e).__name__} → {str(e)}")
        return {}
    finally:
        driver.quit()

# ────────────────────────────────────────────────
# GŁÓWNA LOGIKA
# ────────────────────────────────────────────────

def run_check():
    known_ids = load_known_ids()
    current_data = get_current_lot_data()

    if not current_data:
        print("Nie udało się pobrać danych – kończę")
        return

    new_ids = set(current_data.keys()) - known_ids

    if new_ids:
        print(f"Znaleziono {len(new_ids)} nowych aukcji!")
        new_links = [current_data[i] for i in new_ids]

        # Przygotuj wiadomość
        msg = f"<b>Nowe aukcje dla Ciebie ({len(new_ids)}):</b>\n\n"
        for link in new_links:
            msg += f"➜ {link}\n\n"

        send_telegram_message(msg)

        # Dopisz nowe ID
        append_new_ids(new_ids)
    else:
        print("Brak nowych aukcji")

if __name__ == "__main__":
    run_check()




