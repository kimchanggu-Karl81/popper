import yfinance as yf
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime

def get_data():
    ticker = "^TNX"
    data = yf.download(ticker, period="1y", interval="1d")
    return data

def create_plot(data):
    plt.figure(figsize=(12, 6))
    plt.plot(data['Close'], color='#003366', linewidth=2)
    plt.title(f"US 10Y Treasury Yield", fontsize=16, fontweight='bold')
    plt.ylabel("Yield (%)")
    plt.grid(True, linestyle=':', alpha=0.6)
    last_val = data['Close'].iloc[-1]
    last_date = data.index[-1]
    plt.annotate(f"{last_val:.2f}%", (last_date, last_val), xytext=(10, 5), textcoords='offset points')
    plt.savefig("chart.png", bbox_inches='tight')

def send_telegram(last_val):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    message = f"📊 [US 10Y Yield Report]\nLatest: {last_val:.2f}%"
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open("chart.png", "rb") as photo:
        requests.post(url, data={'chat_id': chat_id, 'caption': message}, files={'photo': photo})

if __name__ == "__main__":
    df = get_data()
    if not df.empty:
        current_yield = df['Close'].iloc[-1]
        create_plot(df)
        send_telegram(current_yield)
