import requests
BOT_TOKEN = "6716660270:AAFB-Fq-B2r6pA574y0CgIYjaPaoJAXpzIk"
CHAT_ID = "-1001954100055"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",        # ⚡ MUST BE HTML
        "disable_web_page_preview": True
    }

    try:
        r = requests.post(url, json=payload, timeout=10)  # ⚡ use json=payload, not data=payload
        r.raise_for_status()
        print("✅ Telegram sent successfully")
        print("Response:", r.text)
    except requests.exceptions.RequestException as e:
        print("❌ Telegram failed:", e)
