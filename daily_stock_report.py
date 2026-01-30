import yfinance as yf
import requests
import os
from datetime import datetime
import re
from collections import Counter

# 환경 변수 (GitHub Secrets)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_stock_info(ticker):
    try:
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) < 2: return "N/A", "0.00%", ""
        curr = data['Close'].iloc[-1]
        prev = data['Close'].iloc[-2]
        change = ((curr - prev) / prev) * 100
        mark = "▲" if change > 0 else "▼" if change < 0 else ""
        price_fmt = f"{curr:,.0f}" if ".KS" in ticker or ".KQ" in ticker else f"{curr:,.2f}"
        return price_fmt, f"{change:+.2f}%", mark
    except:
        return "N/A", "0.00%", ""

def get_market_topics():
    """뉴스 제목의 구조를 분석하여 주요 시장 이슈(주제)를 추출"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://finance.yahoo.com/rss/topstories"
        response = requests.get(url, headers=headers, timeout=10)
        
        # 뉴스 제목 수집
        titles = re.findall(r"<title>(.*?)</title>", response.text)[2:15]
        
        # 핵심 주체(Entity)와 상황(Action) 리스트
        entities = ['FED', 'APPLE', 'NVIDIA', 'BITCOIN', 'STOCKS', 'TESLA', 'INFLATION', 'RATES', 'MARKET', 'TECH', 'AI', 'OIL', 'GOLD']
        actions = ['RISE', 'FALL', 'SURGE', 'JUMP', 'PAUSE', 'CUT', 'CRASH', 'EARNINGS', 'GROWTH', 'DEAL', 'SETTLE', 'HIKE']
        
        topics = []
        for title in titles:
            upper_title = title.upper()
            # 제목에서 핵심 단어 2개 이상 조합 추출
            found_entities = [e for e in entities if e in upper_title]
            found_actions = [a for a in actions if a in upper_title]
            
            if found_entities:
                main_topic = found_entities[0]
                context = found_actions[0] if found_actions else "TRENDING"
                topics.append(f"#{main_topic}_{context}")
        
        # 중복 제거 및 상위 주제 선정
        unique_topics = list(dict.fromkeys(topics))[:10]
        
        if not unique_topics:
            return "🔍 현재 시장을 주도하는 특정 대형 이슈 없음"
            
        return "  ".join(unique_topics)
    except:
        return "⚠️ 주제 분석 데이터 로딩 실패"

def get_realtime_news():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://finance.yahoo.com/rss/topstories"
        response = requests.get(url, headers=headers, timeout=10)
        titles = re.findall(r"<title>(.*?)</title>", response.text)[2:8]
        links = re.findall(r"<link>(.*?)</link>", response.text)[2:8]
        news_text = ""
        for i, (title, link) in enumerate(zip(titles, links)):
            clean_title = title.replace("<![CDATA[", "").replace("]]>", "").strip()
            news_text += f"{i+1}. {clean_title}\n   [기사원문]({link})\n"
        return news_text
    except:
        return "⚠️ 뉴스 로딩 실패\n"

def make_report():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    msg = f"📊 *Smart Market Report ({now})*\n"
    msg += " " + "="*23 + "\n"
    
    # 1. 지수 요약
    indices = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "S&P 500": "^GSPC"}
    for name, ticker in indices.items():
        val, rate, mark = get_stock_info(ticker)
        msg += f"• *{name:.<9}*: {val} ({mark}{rate})\n"

    # 2. 국내 주요 종목
    msg += "\n🇰🇷 *국내 주요 종목*\n"
    stocks = [("전기전자", "005930.KS", "삼성전자"), ("금융", "055550.KS", "신한지주"), ("자동차", "005380.KS", "현대차")]
    for sector, ticker, name in stocks:
        _, rate, _ = get_stock_info(ticker)
        icon = "🔴" if "+" in rate and rate != "0.00%" else "🔵" if "-" in rate else "⚪"
        msg += f"{icon} {name} ({rate})\n"

    # 3. 🔥 시장 주도 이슈 (단어가 아닌 주제 중심)
    msg += "\n🗣️ *WHAT PEOPLE ARE TALKING ABOUT*\n"
    msg += f"_{get_market_topics()}_\n"
    
    # 4. 실시간 뉴스 요약 (제목 + 링크 구조)
    msg += "\n📰 *최신 헤드라인 요약*\n"
    msg += get_realtime_news()
    
    msg += "\n🚀 *주목 ETF*\n"
    etfs = [("미국AI", "NVDX", "Nvidia 2x"), ("한국AI", "471150.KS", "AI반도체")]
    for category, ticker, name in etfs:
        _, rate, mark = get_stock_info(ticker)
        msg += f"▫️ `{category:.<5}` {name} ({mark}{rate})\n"

    msg += "\n" + "="*25
    return msg

def send_telegram():
    report_text = make_report()
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": report_text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    requests.post(url, json=payload)

if __name__ == "__main__":
    send_telegram()
