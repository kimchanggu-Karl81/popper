import yfinance as yf
import requests
import os
from datetime import datetime
import re

# 환경 변수 (GitHub Secrets)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_stock_info(ticker):
    """개별 종목 또는 지수의 현재가와 변동률 가져오기"""
    try:
        data = yf.Ticker(ticker).history(period="2d")
        if len(data) < 2: return "N/A", "0.00%"
        curr = data['Close'].iloc[-1]
        prev = data['Close'].iloc[-2]
        change = ((curr - prev) / prev) * 100
        # 한국 종목(.KS)은 정수, 그 외(미국 등)는 소수점 2자리
        price_fmt = f"{curr:,.0f}" if ".KS" in ticker else f"{curr:,.2f}"
        return price_fmt, f"{change:+.2f}%"
    except:
        return "N/A", "0.00%"

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
        return news_text if news_text else "최신 뉴스가 없습니다.\n"
    except:
        return "⚠️ 뉴스 서비스 로딩 실패\n"

def make_report():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 1. 주요 지수
    indices = {"KOSPI": "^KS11", "KOSPI 200": "^KS200", "S&P 500": "^GSPC", "NASDAQ": "^IXIC"}
    msg = f"📊 *Daily Stocks Briefing ({now})*\n"
    msg += " " + "="*23 + "\n"
    for name, ticker in indices.items():
        val, rate = get_stock_info(ticker)
        msg += f"• *{name}*: {val} ({rate})\n"

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
        _, rate = get_stock_info(ticker)
        rate_val = float(rate.replace('%', ''))
        icon = "🔴" if rate_val > 0 else "🔵" if rate_val < 0 else "⚪"
        fill = max(1, min(5, int(abs(rate_val) + 0.5))) if rate_val != 0 else 0
        bar = "■" * fill + "□" * (5 - fill)
        msg += f"{icon} `{sector:.<5}` {bar} {name}({rate})\n"

    # 3. 뉴스 섹션
    msg += "\n📰 *실시간 주요 경제 뉴스*\n"
    msg += get_realtime_news()

    # 4. 신규 상장 및 주목 ETF (NEW!)
    # 상장된 지 얼마 안 된 종목이나 트렌디한 ETF를 여기에 수동으로 업데이트하세요.
    msg += "\n🚀 *신규 상장 및 주목 ETF*\n"
    etfs = [
        ("미국/AI", "NVDX", "Nvidia 2x"),    # 신규 상장/주목 ETF 예시
        ("미국/반도체", "SOXX", "iShares Semi"),
        ("한국/배당", "482730.KS", "리얼티인컴"), # 국내 신규 상장 예시
        ("한국/AI", "471150.KS", "AI반도체")
    ]
    for category, ticker, name in etfs:
        _, rate = get_stock_info(ticker)
        msg += f"▫️ `{category:.<7}` {name} ({rate})\n"

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
    res = requests.post(url, json=payload)
    if res.status_code != 200:
        payload["parse_mode"] = ""
        requests.post(url, json=payload)

if __name__ == "__main__":
    send_telegram()
