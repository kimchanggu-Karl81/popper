import yfinance as yf
import requests
import os
from datetime import datetime
import re

# 환경 변수 (GitHub Secrets)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_stock_info(ticker):
    """현재가와 변동률 가져오기 및 기호(▲/▼) 적용"""
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

def is_us_market_open():
    """미국 증시 휴장 여부 체크 (MLK Day 등)"""
    # 2026-01-19는 마틴 루터 킹 주니어 날로 휴장
    today = datetime.now().strftime('%Y-%m-%d')
    holidays = ['2026-01-19', '2026-02-16', '2026-04-03'] # 주요 휴장일 예시
    return "🇺🇸 [미국 증시 휴장]" if today in holidays else ""

def get_realtime_news():
    """RSS 피드 실시간 뉴스"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://finance.yahoo.com/rss/topstories"
        response = requests.get(url, headers=headers, timeout=10)
        titles = re.findall(r"<title>(.*?)</title>", response.text)[2:7]
        links = re.findall(r"<link>(.*?)</link>", response.text)[2:7]
        
        news_text = ""
        for i, (title, link) in enumerate(zip(titles, links)):
            clean_title = title.replace("<![CDATA[", "").replace("]]>", "").strip()
            clean_title = re.sub(r'[\[\]\*\(\)_]', '', clean_title)
            news_text += f"{i+1}. [{clean_title}]({link})\n"
        return news_text
    except:
        return "⚠️ 뉴스 로딩 실패\n"

def make_report():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    us_status = is_us_market_open()
    
    # 1. 주요 지수 (KOSDAQ 추가)
    indices = {
        "KOSPI": "^KS11", 
        "KOSPI 200": "^KS200", 
        "KOSDAQ": "^KQ11", 
        "S&P 500": "^GSPC", 
        "NASDAQ": "^IXIC"
    }
    
    msg = f"📊 *Daily Stocks Briefing ({now})*\n"
    if us_status: msg += f" {us_status}\n"
    msg += " " + "="*23 + "\n"
    
    for name, ticker in indices.items():
        val, rate, mark = get_stock_info(ticker)
        msg += f"• *{name:.<10}*: {val} ({mark}{rate})\n"

    # 2. 국내 주요 종목 현황
    msg += "\n🇰🇷 *국내 주요 종목 현황*\n"
    stocks = [
        ("전기전자", "005930.KS", "삼성전자"),
        ("의약품", "207940.KS", "삼성바이오"),
        ("금융", "055550.KS", "신한지주"),
        ("운수장비", "005380.KS", "현대차"),
        ("화학", "051910.KS", "LG화학")
    ]
    for sector, ticker, name in stocks:
        _, rate, _ = get_stock_info(ticker)
        rate_val = float(rate.replace('%', ''))
        icon = "🔴" if rate_val > 0 else "🔵" if rate_val < 0 else "⚪"
        fill = max(1, min(5, int(abs(rate_val) + 0.5))) if rate_val != 0 else 0
        bar = "■" * fill + "□" * (5 - fill)
        msg += f"{icon} `{sector:.<5}` {bar} {name}({rate})\n"

    # 3. 뉴스 섹션
    msg += "\n📰 *실시간 주요 경제 뉴스*\n"
    msg += get_realtime_news()

    # 4. 신규 상장 및 주목 ETF (디테일 강화)
    msg += "\n🚀 *신규 상장 및 주목 ETF*\n"
    etfs = [
        ("미국/AI", "NVDX", "Nvidia 2x"),
        ("미국/반도체", "SOXX", "iShares Semi"),
        ("한국/배당", "482730.KS", "리얼티인컴"),
        ("한국/AI", "471150.KS", "AI반도체")
    ]
    for category, ticker, name in etfs:
        _, rate, mark = get_stock_info(ticker)
        # ETF는 볼드체로 강조하여 가독성 업그레이드
        msg += f"▫️ `{category:.<7}` {name} *({mark}{rate})*\n"

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
    requests.post(url, json=payload)

if __name__ == "__main__":
    send_telegram()
