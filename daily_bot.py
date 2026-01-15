import yfinance as yf
import matplotlib.pyplot as plt
import requests
import os

def get_data():
    ticker = "^TNX"
    # group_by='column'을 추가하여 데이터 구조를 단순화합니다.
    data = yf.download(ticker, period="1y", interval="1d", progress=False, group_by='column')
    return data

def create_plot(data):
    plt.figure(figsize=(10, 6))
    
    # MultiIndex 대응: 'Close' 열을 안전하게 추출
    if 'Close' in data.columns:
        close_data = data['Close']
    else:
        # Ticker 이름이 포함된 경우 대응 (예: ('Close', '^TNX'))
        close_data = data.iloc[:, data.columns.get_level_values(0) == 'Close']

    plt.plot(close_data.index, close_data, color='blue', linewidth=2)
    plt.title("US 10Y Treasury Yield", fontsize=15)
    plt.grid(True, alpha=0.3)
    
    last_val = float(close_data.iloc[-1])
    last_date = close_data.index[-1]
    
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
    
    if not os.path.exists("chart.png"):
        print("Error: chart.png file not found.")
        return

    with open("chart.png", "rb") as photo:
        files = {'photo': photo}
        data = {'chat_id': chat_id, 'caption': message}
        response = requests.post(url, data=data, files=files)
        
        # 전송 결과 확인을 위한 로그 추가
        print(f"Telegram Response Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Response Detail: {response.text}")

if __name__ == "__main__":
    try:
        df = get_data()
        if df.empty:
            print("Error: No data downloaded from yfinance.")
        else:
            current_val = create_plot(df)
            send_telegram(current_val)
            print("Bot script finished successfully!")
    except Exception as e:
        print(f"Error occurred: {e}")
