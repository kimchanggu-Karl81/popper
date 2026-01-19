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

def get_realtime_news():
    """실시간 경제 뉴스 가져오기"""
    try:
        # 시장 전체 흐름을 알 수 있는 S&P 500 지수 티커에서 뉴스 추출
        market = yf.Ticker("^GSPC")
        news_list = market.news[:5]  # 최신 뉴스 5개만 추출
        
        if not news_list:
            return "최신 뉴스가 존재하지 않습니다."

        news_text = ""
        for i, news in enumerate(news_list):
            title = news.get('title')
            publisher = news.get('publisher', 'Finance')
            # 뉴스 제목이 너무 길면 자르기
            if len(title) > 45: title = title[:42] + "..."
            news_text += f"{i+1}. {title} ({publisher})\n"
        
        return news_text
    except:
        return "뉴스를 불러오는 중 오류가 발생했습니다."

def make_report():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 1. 주요 지수 섹션
    indices = {
        "KOSPI": "^KS11",
        "KOSPI 200": "^KS200",
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC"
    }
    
    msg = f"📊 *Daily Stocks Briefing ({now} KST)*\n"
    msg += "="*25 + "\n"
    for name, ticker in indices.items():
        val, rate = get_index_info(ticker)
        msg += f"• *{name}*: {val} ({rate})\n"

    # 2. 업종별 요약 (이 부분은 유지하되 최신 흐름 반영 문구 추가)
    msg += "\n📈 *시장 주요 섹터 흐름 (주간)*\n"
    sectors = [
        ("전기전자", "삼성전자", "■■■■□"),
        ("의약품", "삼성바이오", "■■■■■"),
        ("금융", "KB금융", "■■■■□"),
        ("운수장비", "현대차", "■■■□□"),
        ("화학", "LG화학", "■■□□□")
    ]
    
    for name, top_stock, bar in sectors:
        msg += f"`{name:.<5}` {bar} {top_stock}\n"

    # 3. 전일 주요 뉴스 요약 (실시간 데이터로 교체됨)
    msg += "\n📰 *실시간 주요 경제 뉴스*\n"
    msg += get_realtime_news()

    msg += "\n" + "="*25
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
