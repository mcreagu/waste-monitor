import os
import requests
import json
from datetime import datetime
import time

# --- CONFIGURATION ---
# We use .get() with defaults so it doesn't crash if env vars are missing
ORION_HOST = os.getenv('ORION_HOST', '172.21.32.104')
ORION_PORT = os.getenv('ORION_PORT', '1026')
ENTITY_ID = os.getenv('ENTITY_ID', 'urn:ngsi-ld:WasteContainer:67-49-e4-49-70-22-00-28') #Waste Container 001 by default

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_entity_data():
    url = f"http://{ORION_HOST}:{ORION_PORT}/ngsi-ld/v1/entities/{ENTITY_ID}"
    headers = { "Accept": "application/ld+json" }
    
    print(f"[-] Fetching data from: {url}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print("[+] Orion Data Received.")
        return response.json()
    except Exception as e:
        print(f"[!] ORION FAILED: {e}")
        return None

def format_message(entity_data):
    """Formats the message (Plain Text to avoid Markdown errors)"""
    
    # Safely get values
    def get_val(key):
        val = entity_data.get(key, 'N/A')
        if isinstance(val, dict):
             return val.get('value', 'N/A')
        return val

    fill_level = get_val('fillingLevel')
    threshold = get_val('maxFillingLevelThreshold')
    
    # Constructing the message 
    lines = []
    lines.append("🚨 URGENT: COLLECTION REQUIRED 🚨")
    lines.append(f"The Waste Container has reached its capacity.")
    lines.append("")
    lines.append(f"ID: {ENTITY_ID}")
    lines.append(f"Fill Level: {fill_level} (Threshold: {threshold})")
    lines.append("")
    lines.append("--- Details ---")
    lines.append(f"Temp: {get_val('temperature')} C")
    lines.append(f"Battery: {get_val('battery')}%")
    lines.append(f"Tilt: {get_val('tiltStatus')}")
    lines.append("")
    lines.append(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    
    return "\n".join(lines)

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")
        print("    Did you forget to run 'export TELEGRAM_...=' again?")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
        # "parse_mode": "Markdown" <--- REMOVED to prevent errors
    }

    print(f"[-] Sending to Telegram Chat ID: {TELEGRAM_CHAT_ID}...")
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        # Check if Telegram rejected it
        if response.status_code != 200:
            print(f"[!] TELEGRAM API ERROR: {response.text}")
        else:
            print("[+] SUCCESS: Message sent!")
            
    except Exception as e:
        print(f"[!] CONNECTION ERROR: {e}")

if __name__ == "__main__":
    print("[-] Service started. Monitoring Waste Container (Default interval: 30 mins)...")
    # Check credentials first
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️  WARNING: No Bot Token found. Please export TELEGRAM_BOT_TOKEN.")
    
    while True:
        # --- 1. Do the work ---
        print(f"\n[-] Running check at {datetime.now().strftime('%H:%M:%S')}...")
        data = get_entity_data()
        if data:
            msg = format_message(data)
            print("\n--- PREVIEW ---")
            print(msg)
            print("---------------\n")
            send_telegram(msg)
        # --- 2. Sleep for 30 minutes ---
        print("[-] Sleeping for 30 minutes...")
        time.sleep(1800)  # 1800 seconds = 30 minutes