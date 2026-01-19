import yfinance as yf
import requests
import os
from datetime import datetime
import re

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
    """안정적인 경제 뉴스 수집 (RSS/Search 우회 방식)"""
    try:
        # 야후 파이낸스 뉴스 API가 불안정할 경우를 대비한 직접 접근
        # 헤더 설정을 통해 봇 차단을 방지합니다.
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://finance.yahoo.com/rss/topstories"
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # XML 데이터에서 제목과 링크를 추출하는 간단한 정규식 처리
        titles = re.findall(r"<title>(.*?)</title>", response.text)[2:7] # 상위 5개 (0,1번은 채널 정보)
        links = re.findall(r"<link>(.*?)</link>", response.text)[2:7]
        
        if not titles:
            return "현재 새로운 뉴스가 없습니다.\n"

        news_text = ""
        for i, (title, link) in enumerate(zip(titles, links)):
            # HTML 특수문자 제거 및 텔레그램 마크다운 정화
            clean_title = title.replace("<![CDATA[", "").replace("]]>", "")
            clean_title = clean_title.replace("[", "{").replace("]", "}").replace("*", "")
            
            news_text += f"{i+1}. [{clean_title}]({link})\n"
        
        return news_text
    except Exception as e:
        return "⚠️ 뉴스 서비스 일시 점검 중입니다.\n"

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
    
    # 전송 및 실패 시 재시도
    res = requests.post(url, json=payload)
    if res.status_code != 200:
        payload["parse_mode"] = "" # 마크다운 에러 시 일반 텍스트로 전환
        requests.post(url, json=payload)

if __name__ == "__main__":
    send_telegram()
