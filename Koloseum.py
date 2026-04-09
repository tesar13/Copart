from playwright.sync_api import sync_playwright
import random
import time
import os
from datetime import datetime
import requests  # tylko do Telegrama

URL = "https://ticketing.colosseo.it/en/eventi/full-experience-sotterranei-e-arena"

def human_scroll(page):
    """Symuluje ludzkie przewijanie"""
    for _ in range(random.randint(2, 4)):
        page.evaluate("window.scrollBy(0, {})".format(random.randint(300, 700)))
        time.sleep(random.uniform(0.8, 2.2))
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(random.uniform(0.5, 1.5))

def check_tickets():
    time.sleep(random.uniform(3, 7))

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-web-security",
                "--disable-extensions",
            ]
        )

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            viewport={"width": random.randint(1366, 1920), "height": random.randint(768, 1080)},
            locale="en-US",
            timezone_id="Europe/Rome",
            screen={"width": 1920, "height": 1080},
            device_scale_factor=1,
        )

        # Dodatkowe ukrywanie automatyzacji
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            window.chrome = { runtime: {}, loadTimes: () => ({}) };
            Object.defineProperty(screen, 'availWidth', {get: () => 1920});
        """)

        page = context.new_page()
        page.set_extra_http_headers({"sec-ch-ua": '"Chromium";v="134", "Not;A=Brand";v="99"'})

        print(f"[{datetime.now()}] Otwieram stronę...")
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)

        # Czekamy na załadowanie JS + Cloudflare
        page.wait_for_timeout(12000)   # ważne!

        # Symulujemy ludzkie zachowanie
        human_scroll(page)
        page.wait_for_timeout(4000)

        html = page.content().lower()
        size = len(html)
        
        has_selectday = "soldout_day" in html #fragment HTML do wyszukania zmień tutaj tylko

        print(f"Rozmiar HTML: {size:,} bajtów")
        print(f"selectday znaleziony: {has_selectday}")

        if size > 80000 and has_selectday:
            print(f"[{datetime.now()}] ✅ ZNALEZIONO WOLNE BILETY!")

            token = os.getenv("TELEGRAM_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID")
            if token and chat_id:
                requests.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={
                        "chat_id": chat_id,
                        "text": "🚨 <b>WOLNE BILETY NA COLOSSEUM!</b>\n\nFull Experience – Underground + Arena\n🔗 " + URL,
                        "parse_mode": "HTML"
                    }
                )
            browser.close()
            return True
        else:
            print(f"[{datetime.now()}] ❌ Brak wolnych biletów lub nadal Cloudflare")
            browser.close()
            return False


if __name__ == "__main__":
    check_tickets()
