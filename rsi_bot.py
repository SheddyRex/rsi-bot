import requests
import pandas as pd
import time
import os
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from dotenv import load_dotenv
from flask import Flask

load_dotenv()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
    "DOGEUSDT", "ADAUSDT", "MATICUSDT", "LTCUSDT", "AVAXUSDT"
]

RSI_PERIOD = 14
EMA_PERIOD = 200
INTERVAL = "4h"
LIMIT = 210

BINANCE_URL = "https://api.binance.com/api/v3/klines"

# Flask web server for status
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ RSI Bot is online and monitoring."

def fetch_ohlcv(symbol):
    url = f"{BINANCE_URL}?symbol={symbol}&interval={INTERVAL}&limit={LIMIT}"
    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        "time", "open", "high", "low", "close", "volume",
        "_", "_", "_", "_", "_", "_"
    ])
    df["close"] = pd.to_numeric(df["close"])
    return df

def calculate_indicators(df):
    df["rsi"] = RSIIndicator(close=df["close"], window=RSI_PERIOD).rsi()
    df["ema"] = EMAIndicator(close=df["close"], window=EMA_PERIOD).ema_indicator()
    return df

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    requests.post(url, data=data)
    
    print(f"Sending to {TELEGRAM_CHAT_ID} using token {TELEGRAM_TOKEN[:10]}***")


def check_signals():
    print("🔄 Checking RSI conditions...")
    for symbol in SYMBOLS:
        try:
            df = fetch_ohlcv(symbol)
            df = calculate_indicators(df)

            current_rsi = df["rsi"].iloc[-1]
            current_price = df["close"].iloc[-1]
            ema = df["ema"].iloc[-1]

            message = None

            if current_rsi <= 30:
                message = f"🟢 RSI BUY Signal\n{symbol} @ ${current_price:.2f}\nRSI: {current_rsi:.2f}"
            elif current_rsi >= 70:
                message = f"🔴 RSI SELL Signal\n{symbol} @ ${current_price:.2f}\nRSI: {current_rsi:.2f}"

            if message:
                send_telegram_message(message)

        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")

def bot_loop():
    while True:
        check_signals()
        print("✅ Done. Waiting 3 minutes...\n")
        time.sleep(180)

if __name__ == "__main__":
    import threading
    send_telegram_message("🧪 Telegram test message from RSI bot!")

    # Run bot in a background thread
    threading.Thread(target=bot_loop, daemon=True).start()

    # Run Flask web server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
