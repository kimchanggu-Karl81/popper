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
    """뉴스 제목 추출 로직 강화 (No Title 방지)"""
    try:
        market = yf.Ticker("^GSPC")
        raw_news = market.news
        
        if not raw_news:
            return "현재 업데이트된 뉴스가 없습니다.\n"

        news_text = ""
        for i, item in enumerate(raw_news[:5]):
            title, link, publisher = "No Title", "#", "Finance"
            
            # 데이터가 딕셔너리인 경우 (다양한 키값 대응)
            if isinstance(item, dict):
                title = item.get('title') or item.get('content', {}).get('title') or "No Title"
                link = item.get('link') or item.get('content', {}).get('clickThroughUrl', {}).get('url') or "#"
                publisher = item.get('publisher') or "Yahoo Finance"
            # 데이터가 객체인 경우
            else:
                title = getattr(item, 'title', getattr(item, 'summary', "No Title"))
                link = getattr(item, 'link', "#")
                publisher = getattr(item, 'publisher', "Yahoo Finance")

            # 텔레그램 마크다운 에러 방지를 위한 정화
            clean_title = str(title).replace('[', '{').replace(']', '}').replace('(', ' ').replace(')', ' ').replace('*', '')
            
            # 제목이 여전히 No Title인 경우 리스트에서 제외
            if clean_title == "No Title": continue
                
            news_text += f"{i+1}. [{clean_title}]({link}) - _{publisher}_\n"
        
        return news_text if news_text else "최신 뉴스를 가져오는 중입니다...\n"
    except Exception as e:
        return f"⚠️ 뉴스 로딩 지연 (네트워크 확인 필요)\n"

def make_report():
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
        "disable_web_page_preview": True
    }
    
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        # 마크다운 실패 시 일반 텍스트 전송
        payload["parse_mode"] = ""
        requests.post(url, json=payload)

if __name__ == "__main__":
    send_telegram()
