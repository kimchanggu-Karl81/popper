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
    """현재가와 변동률 가져오기 및 기호(▲/▼) 적용"""
    try:
        # 타임아웃 5초 설정으로 실행 지연 방지
        data = yf.Ticker(ticker).history(period="2d", timeout=5)
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
    """뉴스 제목을 분석하여 #대상_상태 조합의 주제 추출"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://finance.yahoo.com/rss/topstories"
        response = requests.get(url, headers=headers, timeout=7)
        titles = re.findall(r"<title>(.*?)</title>", response.text)[2:15]
        
        # 시장 핵심 주체 및 상황 키워드
        entities = ['FED', 'NVIDIA', 'APPLE', 'BITCOIN', 'TESLA', 'INFLATION', 'AI', 'RATES', 'TECH', 'OIL']
        actions = ['RISE', 'FALL', 'SURGE', 'PAUSE', 'CUT', 'JUMP', 'EARNINGS', 'CRASH']
        
        topics = []
        for title in titles:
            upper_t = title.upper()
            found_e = [e for e in entities if e in upper_t]
            found_a = [a for a in actions if a in upper_t]
            if found_e:
                # 주제 조합 생성
                topics.append(f"#{found_e[0]}_{found_a[0] if found_a else 'NEWS'}")
        
        unique_topics = list(dict.fromkeys(topics))[:12]
        return "  ".join(unique_topics) if unique_topics else "#MARKET_QUIET"
    except:
        return "#TREND_ANALYSIS_OFFLINE"

def get_realtime_news():
    """RSS 피드 실시간 뉴스 수집 (에러 방지용 정의)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://finance.yahoo.com/rss/topstories"
        response = requests.get(url, headers=headers, timeout=7)
        titles = re.findall(r"<title>(.*?)</title>", response.text)[2:7]
        links = re.findall(r"<link>(.*?)</link>", response.text)[2:7]
        news_text = ""
        for i, (title, link) in enumerate(zip(titles, links)):
            clean_title = title.replace("<![CDATA[", "").replace("]]>", "").strip()
            clean_title = re.sub(r'[\[\]\*\(\)_]', '', clean_title)
            news_text += f"{i+1}. [{clean_title[:45]}...]({link})\n"
        return news_text
    except:
        return "⚠️ 뉴스 로딩 실패\n"

def is_us_market_open():
    """미국 증시 휴장 여부 체크"""
    today = datetime.now().strftime('%Y-%m-%d')
    holidays = ['2026-01-19', '2026-02-16', '2026-04-03']
    return "🇺🇸 [미국 증시 휴장]" if today in holidays else ""

def make_report():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    us_status = is_us_market_open()
    
    # 1. 지수 정보
    indices = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "S&P 500": "^GSPC"}
    msg = f"📊 *Smart Market Briefing ({now})*\n"
    if us_status: msg += f" {us_status}\n"
    msg += " " + "="*23 + "\n"
    for name, ticker in indices.items():
        val, rate, mark = get_stock_info(ticker)
        msg += f"• *{name:.<10}*: {val} ({mark}{rate})\n"

    # 2. 🔥 시장 주도 이슈 (주제 중심 나열)
    msg += "\n🗣️ *CURRENT HOT TOPICS*\n"
    msg += f"```\n{get_market_topics()}\n```\n"

    # 3. 국내 주요 종목
    msg += "🇰🇷 *국내 주요 종목*\n"
    stocks = [("전기전자", "005930.KS", "삼성전자"), ("자동차", "005380.KS", "현대차"), ("금융", "055550.KS", "신한지주")]
    for sector, ticker, name in stocks:
        _, rate, _ = get_stock_info(ticker)
        icon = "🔴" if "+" in rate and rate != "0.00%" else "🔵" if "-" in rate else "⚪"
        msg += f"{icon} {name} ({rate})\n"

    # 4. 뉴스 섹션
    msg += "\n📰 *실시간 주요 경제 뉴스*\n"
    msg += get_realtime_news()

    msg += "\n" + "="*25
    return msg

def send_telegram():
    if not TOKEN or not CHAT_ID:
        print("Error: 환경 변수(TOKEN/CHAT_ID)가 설정되지 않았습니다.")
        return
    try:
        report_text = make_report()
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": report_text, "parse_mode": "Markdown", "disable_web_page_preview": True}
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("성공: 텔레그램 리포트가 발송되었습니다.")
    except Exception as e:
        print(f"실패: {e}")

if __name__ == "__main__":
    send_telegram()
