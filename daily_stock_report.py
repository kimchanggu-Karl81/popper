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
    """지수/종목 정보 수집 (타임아웃 설정으로 지연 방지)"""
    try:
        data = yf.Ticker(ticker).history(period="2d", timeout=5)
        if data.empty or len(data) < 2: return "N/A", "0.00%", ""
        curr, prev = data['Close'].iloc[-1], data['Close'].iloc[-2]
        change = ((curr - prev) / prev) * 100
        mark = "▲" if change > 0 else "▼" if change < 0 else ""
        price_fmt = f"{curr:,.0f}" if ".KS" in ticker or ".KQ" in ticker else f"{curr:,.2f}"
        return price_fmt, f"{change:+.2f}%", mark
    except:
        return "N/A", "0.00%", ""

def get_market_topics():
    """뉴스 제목 분석을 통해 '주체+상황' 조합의 주제(Topic) 추출"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = "https://finance.yahoo.com/rss/topstories"
        response = requests.get(url, headers=headers, timeout=7)
        titles = re.findall(r"<title>(.*?)</title>", response.text)[2:15]
        
        # 분석 사전 (시장의 주체와 상황)
        entities = ['FED', 'NVIDIA', 'APPLE', 'BITCOIN', 'TESLA', 'INFLATION', 'AI', 'RATES', 'TECH']
        actions = ['RISE', 'FALL', 'SURGE', 'PAUSE', 'CUT', 'JUMP', 'EARNINGS', 'CRASH']
        
        topics = []
        for title in titles:
            upper_t = title.upper()
            found_e = [e for e in entities if e in upper_t]
            found_a = [a for a in actions if a in upper_t]
            if found_e:
                # 주체 + 상황 조합 (상황이 없으면 NEWS로 표기)
                topics.append(f"#{found_e[0]}_{found_a[0] if found_a else 'NEWS'}")
        
        # 중복 제거 후 최대 10개 나열
        unique_topics = list(dict.fromkeys(topics))[:10]
        return "  ".join(unique_topics) if unique_topics else "🔍 진행 중인 특별한 대형 이슈 없음"
    except:
        return "⚠️ 트렌드 분석 일시 불가능"

def make_report():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    msg = f"📊 *Market Intelligence Report ({now})*\n"
    msg += " " + "="*23 + "\n"
    
    # 1. 주요 지수
    indices = {"KOSPI": "^KS11", "NASDAQ": "^IXIC", "S&P 500": "^GSPC"}
    for name, ticker in indices.items():
        val, rate, mark = get_stock_info(ticker)
        msg += f"• *{name:.<9}*: {val} ({mark}{rate})\n"

    # 2. 국내 주요 종목
    msg += "\n🇰🇷 *국내 주요 종목 현황*\n"
    stocks = [("전기전자", "005930.KS", "삼성전자"), ("의약품", "207940.KS", "삼성바이오"), ("금융", "055550.KS", "신한지주"), ("운수장비", "005380.KS", "현대차"), ("화학", "051910.KS", "LG화학")]
    for sector, ticker, name in stocks:
        _, rate, _ = get_stock_info(ticker)
        rate_val = float(rate.replace('%', ''))
        icon = "🔴" if rate_val > 0 else "🔵" if rate_val < 0 else "⚪"
        fill = max(1, min(5, int(abs(rate_val) + 0.5))) if rate_val != 0 else 0
        bar = "■" * fill + "□" * (5 - fill)
        msg += f"{icon} `{sector:.<5}` {bar} {name}({rate})\n"
        
    # 3. 🔥 시장 주도 주제 (요청하신 주제 중심 나열)
    msg += "\n🗣️ *CURRENT HOT TOPICS*\n"
    msg += f"```\n{get_market_topics()}\n```\n"

    # 4. 뉴스 섹션
    msg += "\n📰 *실시간 주요 경제 뉴스*\n"
    msg += get_realtime_news()

    # 5. ETF 섹션
    msg += "\n🚀 *신규 상장 및 주목 ETF*\n"
    etfs = [("미국/AI", "NVDX", "Nvidia 2x"), ("미국/반도체", "SOXX", "iShares Semi"), ("한국/배당", "482730.KS", "리얼티인컴"), ("한국/AI", "471150.KS", "AI반도체")]
    for category, ticker, name in etfs:
        _, rate, mark = get_stock_info(ticker)
        msg += f"▫️ `{category:.<7}` {name} *({mark}{rate})*\n"

    msg += "\n" + "="*25
    return msg

def send_telegram():
    report_text = make_report()
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": report_text, "parse_mode": "Markdown", "disable_web_page_preview": True}
    requests.post(url, json=payload)

if __name__ == "__main__":
    send_telegram()
