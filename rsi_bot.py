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

# Expanded MEME COINS list (verified on Binance)
SYMBOLS = [
    "DOGEUSDT", "SHIBUSDT", "PEPEUSDT", "FLOKIUSDT",
    "BONKUSDT", "1000SATSUSDT", "1000FLOKIUSDT", "1000SHIBUSDT",
    "1000PEPEUSDT", "WIFUSDT", "MEMEUSDT"
]

# Adjusted indicators for faster meme coin signals
RSI_PERIOD = 7
EMA_PERIOD = 50
INTERVAL = "15m"
LIMIT = 100

BINANCE_URL = "https://api.binance.com/api/v3/klines"

# Flask web server for status
app = Flask(__name__)

@app.route("/")
def home():
    return f"""
    <html>
        <head>
            <title>RSI Meme Bot Status</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f4f4f4; padding: 40px; }}
                .status-box {{ background: white; padding: 20px; max-width: 500px; margin: auto; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                .status {{ font-size: 24px; color: green; }}
            </style>
        </head>
        <body>
            <div class="status-box">
                <h2>🐶 RSI Meme Bot Status</h2>
                <p class="status">✅ Online and scanning meme coins</p>
                <p>Tracking symbols: {', '.join(SYMBOLS)}</p>
                <p>Check interval: Every 5 minutes (15m candles)</p>
            </div>
        </body>
    </html>
    """

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
    print(f"🚀 Sent to Telegram: {message}")

def check_signals():
    print("🔍 Checking RSI/EMA signals for meme coins...")
    for symbol in SYMBOLS:
        try:
            df = fetch_ohlcv(symbol)
            df = calculate_indicators(df)

            current_rsi = df["rsi"].iloc[-1]
            current_price = df["close"].iloc[-1]
            current_ema = df["ema"].iloc[-1]

            # BUY: Strong oversold & above EMA trend
            if current_rsi <= 25 and current_price > current_ema:
                message = (f"🟢 MEME BUY SIGNAL\n"
                           f"Symbol: {symbol}\n"
                           f"Price: ${current_price:.5f}\n"
                           f"RSI: {current_rsi:.2f} (≤25)\n"
                           f"EMA({EMA_PERIOD}): ${current_ema:.5f}")
                send_telegram_message(message)

            # SELL: Strong overbought & below EMA trend
            elif current_rsi >= 75 and current_price < current_ema:
                message = (f"🔴 MEME SELL SIGNAL\n"
                           f"Symbol: {symbol}\n"
                           f"Price: ${current_price:.5f}\n"
                           f"RSI: {current_rsi:.2f} (≥75)\n"
                           f"EMA({EMA_PERIOD}): ${current_ema:.5f}")
                send_telegram_message(message)

        except Exception as e:
            print(f"❌ Error with {symbol}: {e}")

def bot_loop():
    while True:
        check_signals()
        print("✅ Done. Waiting 5 minutes...\n")
        time.sleep(300)  # 5 minutes

if __name__ == "__main__":
    import threading
    send_telegram_message("🚀 Meme Bot started and connected to Telegram!")

    # Start bot in a background thread
    threading.Thread(target=bot_loop, daemon=True).start()

    # Run Flask web server
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
