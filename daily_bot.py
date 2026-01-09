import yfinance as yf
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime

# 파이썬 3.9 이하 호환성을 위해 타입 힌트 생략 및 안정적 코드 사용
def get_data():
    ticker = "^TNX"
    # 최신 yfinance의 내부 문법 에러를 피하기 위해 다운로드 방식 변경
    data = yf.download(ticker, period="1y", interval="1d", progress=False)
    return data

def create_plot(data):
    plt.figure(figsize=(10, 6))
    plt.plot(data.index, data['Close'], color='blue', linewidth=2)
    plt.title("US 10Y Treasury Yield", fontsize=15)
    plt.grid(True, alpha=0.3)
    
    last_val = data['Close'].iloc[-1]
    last_date = data.index[-1]
    plt.annotate(f"{last_val:.2f}%", (last_date, last_val), xytext=(10, 0), textcoords='offset points')
    plt.savefig("chart.png")
    return last_val

def send_telegram(val):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("Error: Secrets are not set properly.")
        return

    message = f"📊 [Daily Report]\nUS 10Y Yield: {val:.2f}%"
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    
    with open("chart.png", "rb") as photo:
        requests.post(url, data={'chat_id': chat_id, 'caption': message}, files={'photo': photo})

if __name__ == "__main__":
    try:
        df = get_data()
        current_val = create_plot(df)
        send_telegram(current_val)
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")
