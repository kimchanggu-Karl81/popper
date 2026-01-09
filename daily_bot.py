import yfinance as yf
import matplotlib.pyplot as plt
import requests
import os
from datetime import datetime

# 폰트 깨짐 방지를 위한 기본 설정
plt.rcParams['figure.figsize'] = (12, 6)

def get_data():
    # 미국채 10년물 티커
    data = yf.download("^TNX", period="1y", interval="1d")
    return data

def create_plot(data):
    plt.figure()
    plt.plot(data['Close'], color='#003366', linewidth=2)
    plt.title("US 10Y Treasury Yield (1 Year)", fontsize=16)
    plt.grid(True, linestyle=':', alpha=0.6)
    
    last_val = float(data['Close'].iloc[-1])
    last_date = data.index[-1]
    
    plt.annotate(f"{last_val:.2f}%", (last_date, last_val), 
                 xytext=(10, 0), textcoords='offset points', fontweight='bold')
    plt.savefig("chart.png", bbox_inches='tight')
    return last_val

def send_telegram(yield_val):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    # 10자 이내 뉴스 요약 (수동 예시)
    news = "미 고용 호조 금리 반등"
    
    message = f"📊 [미국채 10년물 리포트]\n금리: {yield_val:.2f}%\n이슈: {news}"
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open("chart.png", "rb") as photo:
        requests.post(url, data={'chat_id': chat_id, 'caption': message}, files={'photo': photo})

if __name__ == "__main__":
    try:
        df = get_data()
        current_yield = create_plot(df)
        send_telegram(current_yield)
        print("전송 완료!")
    except Exception as e:
        print(f"에러 발생: {e}")
