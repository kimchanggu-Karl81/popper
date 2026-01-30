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
    """뉴스 분석 후 키워드별 언급 횟수를 막대그래프로 시각화 (상위 15개)"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # 다각화된 분석을 위해 주요 경제 뉴스 피드 2곳 활용
        urls = ["https://finance.yahoo.com/rss/topstories", "https://finance.yahoo.com/rss/stocks"]
        
        all_titles = []
        for url in urls:
            response = requests.get(url, headers=headers, timeout=10)
            titles = re.findall(r"<title>(.*?)</title>", response.text)[2:]
            all_titles.extend(titles)
            
        full_text = " ".join(all_titles).upper()
        # 4글자 이상의 영문 대문자 단어만 추출
        words = re.findall(r'\b[A-Z]{4,}\b', full_text)
        
        # 금융 뉴스용 불용어 필터링
        stopwords = {
            'THE', 'AND', 'FOR', 'STOCKS', 'MARKET', 'WITH', 'FROM', 'THIS', 'STOCK', 
            'WILL', 'ARE', 'SAYS', 'REPORT', 'YEAR', 'TIME', 'ABOUT', 'AFTER', 'COULD',
            'FIRST', 'MORE', 'INTO', 'THEIR', 'WHAT', 'THESE', 'WHICH'
        }
        filtered_words = [w for w in words if w not in stopwords]
        
        # 상위 15개 키워드 추출
        counts = Counter(filtered_words).most_common(15)
        if not counts: return "🔍 데이터가 부족하여 트렌드를 분석할 수 없습니다."

        max_count = counts[0][1]
        trend_msg = ""
        
        for word, count in counts:
            # 언급 빈도에 따라 최대 8칸의 막대 생성
            bar_len = int((count / max_count) * 8)
            bar = "■" * bar_len + "□" * (8 - bar_len)
            # 가독성을 위해 키워드 길이를 12자로 고정하여 정렬
            trend_msg += f"`{word:.<12}` {bar} ({count})\n"
            
        return trend_msg
    except:
        return "⚠️ 트렌드 분석 중 오류가 발생했습니다."

def is_us_market_open():
    """미국 증시 휴장 여부 체크"""
    today = datetime.now().strftime('%Y-%m-%d')
    holidays = ['2026-01-19', '2026-02-16', '2026-04-03']
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
    
    # 1. 지수 정보
    indices = {"KOSPI": "^KS11", "KOSDAQ": "^KQ11", "S&P 500": "^GSPC", "NASDAQ": "^IXIC"}
    msg = f"📊 *Daily Stocks Briefing ({now})*\n"
    if us_status: msg += f" {us_status}\n"
    msg += " " + "="*23 + "\n"
    for name, ticker in indices.items():
        val, rate, mark = get_stock_info(ticker)
        msg += f"• *{name:.<10}*: {val} ({mark}{rate})\n"

    # 2. 🔥 실시간 시장 핫 트렌드 (15개 키워드 시각화)
    # 기존 밸류에이션 분석 섹션을 대체합니다.
    msg += "\n🔥 *실시간 주요 키워드 언급 빈도*\n"
    msg += get_visual_trends()

    # 3. 국내 주요 종목
    msg += "\n🇰🇷 *국내 주요 종목 현황*\n"
    stocks = [("전기전자", "005930.KS", "삼성전자"), ("의약품", "207940.KS", "삼성바이오"), ("금융", "055550.KS", "신한지주"), ("운수장비", "005380.KS", "현대차"), ("화학", "051910.KS", "LG화학")]
    for sector, ticker, name in stocks:
        _, rate, _ = get_stock_info(ticker)
        rate_val = float(rate.replace('%', ''))
        icon = "🔴" if rate_val > 0 else "🔵" if rate_val < 0 else "⚪"
        fill = max(1, min(5, int(abs(rate_val) + 0.5))) if rate_val != 0 else 0
        bar = "■" * fill + "□" * (5 - fill)
        msg += f"{icon} `{sector:.<5}` {bar} {name}({rate})\n"

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
