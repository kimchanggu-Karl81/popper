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
        return f"{curr:,.0f}" if ".KS" in ticker else f"{curr:,.2f}", f"{change:+.2f}%"
    except:
        return "N/A", "0.00%"

def get_realtime_news():
    """RSS 피드를 활용한 실시간 뉴스 (링크 최적화)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://finance.yahoo.com/rss/topstories"
        response = requests.get(url, headers=headers, timeout=10)
        
        titles = re.findall(r"<title>(.*?)</title>", response.text)[2:7]
        links = re.findall(r"<link>(.*?)</link>", response.text)[2:7]
        
        news_text = ""
        for i, (title, link) in enumerate(zip(titles, links)):
            clean_title = title.replace("<![CDATA[", "").replace("]]>", "").strip()
            # 특수문자 제거하여 마크다운 에러 방지
            clean_title = re.sub(r'[\[\]\*\(\)_]', '', clean_title)
            # [제목](링크) 형식
            news_text += f"{i+1}. [{clean_title}]({link})\n"
        
        return news_text if news_text else "최신 뉴스가 없습니다.\n"
    except:
        return "⚠️ 뉴스 서비스를 불러올 수 없습니다.\n"

def make_report():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    # 1. 지수 정보 (실시간)
    indices = {"KOSPI": "^KS11", "KOSPI 200": "^KS200", "S&P 500": "^GSPC", "NASDAQ": "^IXIC"}
    msg = f"📊 *Daily Stocks Briefing ({now})*\n"
    msg += " " + "="*23 + "\n"
    for name, ticker in indices.items():
        val, rate = get_stock_info(ticker)
        msg += f"• *{name}*: {val} ({rate})\n"

    # 2. 한국 주요 종목 실시간 수익률
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
        # 수익률에 따른 바 그래프 표시 (간이 시각화)
        rate_val = float(rate.replace('%', ''))
        bar = "■" * max(1, min(5, int(abs(rate_val) + 2)))
        msg += f"`{sector:.<5}` {bar.ljust(5, '□')} {name}({rate})\n"

    # 3. 뉴스 섹션
    msg += "\n📰 *실시간 주요 경제 뉴스 (클릭)*\n"
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
    
    res = requests.post(url, json=payload)
    if res.status_code != 200:
        # 실패 시 마크다운 없이 재시도
        payload["parse_mode"] = ""
        requests.post(url, json=payload)

if __name__ == "__main__":
    send_telegram()
