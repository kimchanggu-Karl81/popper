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
    """실시간 경제 뉴스 가져오기 (데이터 구조 변화 완벽 대응)"""
    try:
        # 시장 지수 뉴스 호출
        market = yf.Ticker("^GSPC")
        raw_news = market.news
        
        if not raw_news:
            return "현재 업데이트된 뉴스가 없습니다.\n"

        news_text = ""
        # 상위 5개 뉴스 추출
        for i, item in enumerate(raw_news[:5]):
            try:
                # 1. 데이터 추출 (딕셔너리 및 객체 형태 모두 대응)
                if isinstance(item, dict):
                    title = item.get('title', 'No Title')
                    link = item.get('link', '#')
                    publisher = item.get('publisher', 'Finance')
                else:
                    # 속성으로 접근 시도 (getattr 사용으로 에러 방지)
                    title = getattr(item, 'title', 'No Title')
                    link = getattr(item, 'link', '#')
                    publisher = getattr(item, 'publisher', 'Finance')

                # 2. Markdown 특수문자 정화 (에러의 주요 원인)
                # 텔레그램 Markdown에서 [], (), * 등은 예약어이므로 제거하거나 대체해야 함
                clean_title = title.replace('[', '{').replace(']', '}').replace('(', ' ').replace(')', ' ').replace('*', '')
                
                # 3. 메시지 생성
                news_text += f"{i+1}. [{clean_title}]({link}) - _{publisher}_\n"
            except:
                continue
        
        return news_text if news_text else "뉴스를 구성하는 중 오류가 발생했습니다.\n"
    except Exception as e:
        print(f"DEBUG - News Function Error: {e}")
        return "⚠️ 최신 뉴스를 불러올 수 없습니다. (API 통신 오류)\n"

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
        "parse_mode": "Markdown", # 혹은 "HTML"로 변경 가능
        "disable_web_page_preview": True
    }
    
    response = requests.post(url, json=payload)
    # 만약 Markdown 에러로 실패할 경우 일반 텍스트로 재시도
    if response.status_code != 200:
        payload["parse_mode"] = ""
        requests.post(url, json=payload)
        print(f"전송 재시도 (Markdown 오류 가능성): {response.text}")
    else:
        print("Telegram 리포트 전송 성공!")

if __name__ == "__main__":
    send_telegram()
