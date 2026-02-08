from DrissionPage import ChromiumPage, ChromiumOptions
import time
import re
import os
import requests
import random

# --- KONFIGURATION ---
WEBHOOK_URL = "https://discord.com/api/webhooks/1412624972710543461/57HmSvQfR0TfnoKk1KPK5begZSxvsdVUlHp1f1u482HLCTrloDyVmF9x4mrAwKotUV4h"
LOG_FILE = "ergebnisse.txt"
MIN_PRICE = 0
MAX_PRICE = 30

BASE_URL = f"https://lzt.market/roblox/?min_price={MIN_PRICE}&max_price={MAX_PRICE}&order_by=pdate_to_down"

def get_browser():
    co = ChromiumOptions()
    # Wir lassen Stylesheets jetzt mal drin, damit die Seite korrekt "geladen" wird für den Klick-Sim
    co.set_pref('profile.managed_default_content_settings.images', 2) 
    return ChromiumPage(co)

def load_memory():
    ids = set()
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                match = re.search(r'ID: (\d+)', line)
                if match: ids.add(match.group(1))
    return ids

def save_to_memory(name, item_id):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"ID: {item_id} | Name: {name} | Zeit: {time.strftime('%H:%M:%S')}\n")

def scan_full_page_for_name(page):
    """Scannt die Biografie und alle Texte auf der Detailseite."""
    try:
        # Wir holen uns den Text aus der Biografie/Beschreibung und dem Header
        # .itemDescription ist oft die Box, wo der Verkäufer was reinschreibt
        bio_text = ""
        if page.ele('.itemDescription'):
            bio_text = page.ele('.itemDescription').text
        
        main_text = page.ele('tag:body').text
        
        full_content = f"{page.title} {bio_text} {main_text}"
        
        # Suche nach 3-6 Zeichen (Buchstaben & Zahlen)
        blacklist = {"roblox", "account", "random", "mail", "access", "premium", "robux", "level", "cheap", "verified", "stock", "years", "skins"}
        words = re.findall(r'\b[a-zA-Z0-9]{3,6}\b', full_content)
        
        for word in words:
            if word.lower() not in blacklist and not word.isdigit() and re.search(r'[a-zA-Z]', word):
                return word
    except:
        pass
    return None

def run_sniper():
    page = get_browser()
    gecheckte_ids = load_memory()

    print(f"[🚀] Deep-Bio Sniper gestartet.")
    page.get(BASE_URL)
    input(">>> Bitte einloggen und ENTER drücken <<<")

    current_page = 1
    
    while True:
        print(f"\n--- 📄 SCANNE SEITE {current_page} ---")
        page.get(f"{BASE_URL}&page={current_page}")
        time.sleep(2) # Warten auf Liste
        
        items = page.eles('.marketListItem')
        
        if not items:
            print("[*] Keine weiteren Angebote auf dieser Seite. Zurück zu Seite 1...")
            current_page = 1
            time.sleep(10)
            continue

        for item in items:
            try:
                item_id = item.attr('id').replace('item-', '')
            except: continue

            if item_id in gecheckte_ids:
                continue

            print(f"[*] Öffne Account {item_id}...")
            
            # Jetzt wird "draufgeklickt" (per URL-Navigation, was sicherer ist)
            # Das Skript verlässt die Liste und geht IN den Account
            page.get(f"https://lzt.market/{item_id}/")
            
            # Intensiver Scan der Biografie
            name = scan_full_page_for_name(page)
            
            if name:
                print(f"    ✅ NAME GEFUNDEN: {name}")
                save_to_memory(name, item_id)
                requests.post(WEBHOOK_URL, json={
                    "embeds": [{
                        "title": "🎯 Neuer OG Name in Biografie!",
                        "description": f"**Name:** `{name}`\n**ID:** {item_id}\n**Link:** [Angebotsseite](https://lzt.market/{item_id}/)",
                        "color": 3066993
                    }]
                })
            else:
                print(f"    [-] Kein Name in Bio gefunden.")

            gecheckte_ids.add(item_id)
            
            # Zurück zur Liste für das nächste Item
            page.get(f"{BASE_URL}&page={current_page}")
            time.sleep(random.uniform(1.0, 2.0)) # Kurz warten vor dem nächsten

        # Wenn Seite fertig, nächste Seite
        current_page += 1
        print(f"[*] Seite {current_page-1} abgeschlossen. Wechsle zu Seite {current_page}...")

if __name__ == "__main__":
    run_sniper()