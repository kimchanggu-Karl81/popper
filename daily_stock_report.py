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
    """실시간 경제 뉴스 가져오기 (에러 방지 및 링크 추가)"""
    try:
        # S&P 500 지수 티커에서 뉴스 추출
        market = yf.Ticker("^GSPC")
        news_list = market.news
        
        if not news_list:
            return "최신 뉴스가 존재하지 않습니다.\n"

        news_text = ""
        # 상위 5개 뉴스만 처리
        for i, news in enumerate(news_list[:5]):
            # 객체 또는 딕셔너리 형태 모두 대응 가능하도록 처리
            title = news.get('title') if isinstance(news, dict) else getattr(news, 'title', 'No Title')
            link = news.get('link') if isinstance(news, dict) else getattr(news, 'link', '#')
            publisher = news.get('publisher', 'Finance') if isinstance(news, dict) else getattr(news, 'publisher', 'Finance')

            # Markdown 특수문자 에러 방지 (대괄호 등 제거)
            clean_title = title.replace('[', '').replace(']', '').replace('*', '')
            
            # [제목](링크) 형식으로 클릭 가능하게 구성
            news_text += f"{i+1}. [{clean_title}]({link}) ({publisher})\n"
        
        return news_text
    except Exception as e:
        print(f"News Error Detail: {e}") # 로그 확인용
        return "⚠️ 뉴스를 불러오는 중 오류가 발생했습니다.\n"

def make_report():
    # 현재 시간 (한국 시간 기준)
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
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

    msg += "\n📰 *실시간 주요 경제 뉴스 (클릭 시 이동)*\n"
    msg += get_realtime_news()

    msg += "\n" + "="*25
    return msg

def send_telegram():
    report_text = make_report()
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": report_text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True # 링크 미리보기로 메시지가 지저분해지는 것 방지
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Telegram 리포트 전송 성공!")
    else:
        print(f"전송 실패: {response.text}")

if __name__ == "__main__":
    send_telegram()
