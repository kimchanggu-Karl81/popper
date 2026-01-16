import yfinance as yf
import requests
import os
from datetime import datetime

# 환경 변수 (GitHub Secrets)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_index_info(ticker):
    """지수 데이터 가져오기"""
    try:
        data = yf.Ticker(ticker).history(period="5d")
        if data.empty: return "N/A", "0.00%"
        price = data['Close'].iloc[-1]
        prev_price = data['Close'].iloc[-2]
        change = ((price - prev_price) / prev_price) * 100
        return f"{price:,.2f}", f"{change:+.2f}%"
    except:
        return "N/A", "0.00%"

def make_report():
    now = datetime.now().strftime('%Y-%m-%d')
    
    # 1. 주요 지수 섹션
    indices = {
        "KOSPI": "^KS11",
        "KOSPI 200": "^KS200",
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC"
    }
    
    msg = f"📊 *Daily Stocks Briefing ({now})*\n"
    msg += "="*25 + "\n"
    for name, ticker in indices.items():
        val, rate = get_index_info(ticker)
        msg += f"• *{name}*: {val} ({rate})\n"

    # 2. 업종별 상위 종목 (시각화 포함)
    # 실제 운영 시 수익률 데이터를 API로 실시간 계산하도록 확장 가능합니다.
    msg += "\n📈 *업종별 주간 수익률 상위 종목*\n"
    sectors = [
        ("전기전자", "삼성전자(+4.5%)", "■■■■□"),
        ("의약품", "삼성바이오(+5.2%)", "■■■■■"),
        ("금융", "KB금융(+4.8%)", "■■■■□"),
        ("운수장비", "현대차(+3.2%)", "■■■□□"),
        ("음식료", "농심(+3.5%)", "■■■□□"),
        ("건설", "현대건설(+3.2%)", "■■■□□"),
        ("철강", "POSCO홀(+2.2%)", "■■□□□"),
        ("화학", "LG화학(+1.8%)", "■■□□□")
    ]
    
    for name, top_stock, bar in sectors:
        msg += f"`{name:.<5}` {bar} {top_stock}\n"

    # 3. 전일 경제 뉴스 요약
    msg += "\n📰 *전일 주요 뉴스 요약*\n"
    msg += "1. Fed 금리 동결 시그널에 나스닥 강세\n"
    msg += "2. 반도체 HBM 공급 확대 기대감 지속\n"
    msg += "3. 원/달러 환율 1,320원대 안착 성공\n"
    msg += "4. 중국 부양책 발표로 철강/화학 반등\n"

    return msg

def send_telegram():
    report_text = make_report()
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": report_text,
        "parse_mode": "Markdown"
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Telegram 리포트 전송 성공!")
    else:
        print(f"전송 실패: {response.text}")

if __name__ == "__main__":
    send_telegram()
