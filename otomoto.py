import requests
from bs4 import BeautifulSoup
import time
import random
import os

BASE_URL = "https://www.otomoto.pl/osobowe/audi--cupra--kia--skoda/seg-combi--seg-compact--seg-coupe--seg-sedan/od-2015/myslowice?search%5Bdist%5D=100&search%5Bfilter_enum_damaged%5D=0&search%5Bfilter_enum_fuel_type%5D%5B0%5D=diesel&search%5Bfilter_enum_fuel_type%5D%5B1%5D=petrol&search%5Bfilter_enum_gearbox%5D=automatic&search%5Bfilter_float_engine_capacity%3Afrom%5D=1500&search%5Bfilter_float_engine_power%3Afrom%5D=160&search%5Bfilter_float_mileage%3Ato%5D=170000&search%5Bfilter_float_price%3Afrom%5D=40000&search%5Bfilter_float_price%3Ato%5D=70000&search%5Blat%5D=50.24998&search%5Blon%5D=19.13387&search%5Border%5D=created_at_first%3Adesc&search%5Badvanced_search_expanded%5D=true"

SESSION = requests.Session()

MAX_PAGES = 10

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4)"
]


def rotate_headers():
    SESSION.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8",
    })


def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})


def load_ids():
    if not os.path.exists("otomoto.txt"):
        return set()
    with open("otomoto.txt") as f:
        return set(line.strip() for line in f)


def save_ids(ids):
    with open("otomoto.txt", "a") as f:
        for i in ids:
            f.write(i + "\n")


def scrape():
    known = load_ids()
    new_ids = []

    for page in range(1, MAX_PAGES + 1):
        print(f"Strona: {page}")
        rotate_headers()

        url = BASE_URL + f"&page={page}"
        r = SESSION.get(url, timeout=30)

        soup = BeautifulSoup(r.text, "html.parser")
        offers = soup.select("article[data-id]")

        if not offers:
            break

        stop = False

        for offer in offers:
            ad_id = offer.get("data-id")
            link_tag = offer.find("a", href=True)

            if not ad_id or not link_tag:
                continue

            if ad_id in known:
                stop = True
                break

            link = link_tag["href"]
            if not link.startswith("http"):
                link = "https://www.otomoto.pl" + link

            print("NOWE:", link)
            send_telegram(link)

            new_ids.append(ad_id)

        if stop:
            print("STOP: znaleziono znane ID")
            break

        time.sleep(random.uniform(1.5, 3))

    if new_ids:
        save_ids(new_ids)

    print(f"✅ Nowe: {len(new_ids)}")


if __name__ == "__main__":
    scrape()
