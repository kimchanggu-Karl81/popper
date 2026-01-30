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

def get_visual_trends():
    """뉴스 분석 후 키워드별 언급 횟수를 막대그래프로 변환"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        urls = ["https://finance.yahoo.com/rss/topstories", "https://finance.yahoo.com/rss/stocks"]
        
        all_titles = []
        for url in urls:
            response = requests.get(url, headers=headers, timeout=10)
            titles = re.findall(r"<title>(.*?)</title>", response.text)[2:]
            all_titles.extend(titles)
            
        full_text = " ".join(all_titles).upper()
        words = re.findall(r'\b[A-Z]{4,}\b', full_text)
        
        stopwords = {'THE', 'AND', 'FOR', 'STOCKS', 'MARKET', 'WITH', 'FROM', 'THIS', 'STOCK', 'WILL', 'ARE', 'SAYS', 'REPORT', 'YEAR', 'TIME', 'ABOUT', 'AFTER'}
        filtered_words = [w for w in words if w not in stopwords]
        
        counts = Counter(filtered_words).most_common(10)
        if not counts: return "🔍 트렌드 데이터 없음"

        # 시각화 로직: 가장 많이 언급된 단어를 기준으로 비율 계산
        max_count = counts[0][1]
        trend_msg = ""
        
        for word, count in counts:
            # 언급 횟수에 따른 막대 생성 (최대 8칸)
            bar_len = int((count / max_count) * 8)
            bar = "■" * bar_len + "□" * (8 - bar_len)
            trend_msg += f"`{word:.<12}` {bar} ({count}회)\n"
            
        return trend_msg
    except:
        return "⚠️ 트렌드 분석 중 오류 발생"

def get_realtime_news():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://finance.yahoo.com/rss/topstories"
        response = requests.get(url, headers=headers, timeout=10)
        titles = re.findall(r"<title>(.*?)</title>", response.text)[2:7]
        links = re.findall(r"<link>(.*?)</link>", response.text)[2:7]
        news_text = ""
        for i, (title, link) in enumerate(zip(titles, links)):
            clean_title = title.replace("<![CDATA[", "").replace("]]>", "").strip()
            news_text += f"{i+1}. [{clean_title[:45]}...]({link})\n"
        return news_text
    except:
        return "⚠️ 뉴스 로딩 실패\n"

def make_report():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    msg = f"📊 *Market Trend Briefing ({now})*\n"
    msg += " " + "="*23 + "\n"
    
    # 1. 주요 지수
    indices = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "S&P 500": "^GSPC"}
    for name, ticker in indices.items():
        val, rate, mark = get_stock_info(ticker)
        msg += f"• *{name:.<9}*: {val} ({mark}{rate})\n"

    # 2. 🔥 실시간 트렌드 막대그래프 (NEW)
    msg += "\n🔥 *실시간 키워드 언급 빈도*\n"
    msg += get_visual_trends()

    # 3. 국내 주요 종목
    msg += "\n🇰🇷 *국내 주요 종목*\n"
    stocks = [("반도체", "005930.KS", "삼성전자"), ("자동차", "005380.KS", "현대차"), ("금융", "055550.KS", "신한지주")]
    for sector, ticker, name in stocks:
        _, rate, _ = get_stock_info(ticker)
        icon = "🔴" if "+" in rate and rate != "0.00%" else "🔵" if "-" in rate else "⚪"
        msg += f"{icon} {name}({rate})\n"

    # 4. 실시간 뉴스 요약
    msg += "\n📰 *실시간 주요 경제 뉴스*\n" + get_realtime_news()
    
    msg += "\n" + "="*25
    return msg

def send_telegram():
    report_text = make_report()
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": report_text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    requests.post(url, json=payload)

if __name__ == "__main__":
    send_telegram()
