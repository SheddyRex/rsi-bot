import requests
import pandas as pd
import time
import os
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator
from dotenv import load_dotenv
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def status():
    return '✅ RSI Bot is running'

def run_flask():
    app.run(host='0.0.0.0', port=8080)


load_dotenv()


TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# List of popular, highly-liquid crypto symbols (USDT pairs)
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
    "DOGEUSDT", "ADAUSDT", "MATICUSDT", "LTCUSDT", "AVAXUSDT"
]

RSI_PERIOD = 14
EMA_PERIOD = 200
INTERVAL = "4h"  # Binance interval (e.g., "15m", "1h", "4h")
LIMIT = 210      # At least 200 for EMA + buffer

BINANCE_URL = "https://api.binance.com/api/v3/klines"

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

            if current_rsi <= 50:
                message = f"🟢 *RSI BUY Signal*\nSymbol: {symbol}\nPrice: ${current_price:.2f}\nRSI: {current_rsi:.2f} (≤30)"
            elif current_rsi >= 50:
                message = f"🔴 *RSI SELL Signal*\nSymbol: {symbol}\nPrice: ${current_price:.2f}\nRSI: {current_rsi:.2f} (≥70)"

            if message:
                send_telegram_message(message)

        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")

def main_loop():
    while True:
        check_signals()
        print("✅ Done. Waiting 15 minutes...\n")
        time.sleep(900)  # 15 minutes

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Run RSI bot loop
    main_loop()
