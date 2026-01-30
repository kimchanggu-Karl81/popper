import yfinance as yf
import requests
import os
from datetime import datetime
import re
from collections import Counter

# 환경 변수
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_market_topics():
    """뉴스 제목의 패턴을 분석하여 생동감 있는 주제 추출"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # 더 많은 데이터를 위해 RSS 피드 3곳 통합
        urls = [
            "https://finance.yahoo.com/rss/topstories",
            "https://finance.yahoo.com/rss/stocks",
            "https://finance.yahoo.com/rss/news"
        ]
        
        titles = []
        for url in urls:
            res = requests.get(url, headers=headers, timeout=7)
            titles.extend(re.findall(r"<title>(.*?)</title>", res.text)[2:])
        
        # 1. 핵심 주체(Entities) 및 상태(Actions) 확장 리스트
        entities = ['FED', 'NVIDIA', 'APPLE', 'TESLA', 'BITCOIN', 'AI', 'INFLATION', 'RATES', 'TECH', 'OIL', 'GOLD', 'CHINA', 'USA', 'JOBS', 'EARNINGS', 'DEBT', 'REVENUE', 'CEO']
        actions = ['SURGE', 'FALL', 'PAUSE', 'CUT', 'HIKE', 'JUMP', 'CRASH', 'BEAT', 'MISS', 'RALLY', 'SLUMP', 'BOOST', 'HALT', 'DIP', 'CLIMB']
        
        topics = []
        for title in titles:
            t_upper = title.upper()
            # 제목에서 Entity와 Action이 모두 발견되는 경우 조합
            found_e = [e for e in entities if e in t_upper]
            found_a = [a for a in actions if a in t_upper]
            
            if found_e:
                main_e = found_e[0]
                # 구체적인 액션이 있으면 조합, 없으면 제목의 다른 명사 활용 시도
                if found_a:
                    topics.append(f"#{main_e}_{found_a[0]}")
                else:
                    # 액션이 없을 경우 제목에서 4글자 이상의 다른 단어를 하나 더 붙임
                    words = [w for w in re.findall(r'\b[A-Z]{4,}\b', t_upper) if w not in entities and w not in ['WITH', 'FROM', 'THIS', 'THAT']]
                    if words:
                        topics.append(f"#{main_e}_{words[0]}")
                    else:
                        topics.append(f"#{main_e}_NEWS")

        # 2. 중복 제거 및 상위 20개 선정 (빼곡한 나열을 위해 개수 상향)
        unique_topics = list(dict.fromkeys(topics))[:20]
        
        # 3. 신문 1면처럼 보이기 위한 줄바꿈 처리 (4~5개마다 줄바꿈)
        formatted_topics = ""
        for i in range(0, len(unique_topics), 4):
            formatted_topics += "  ".join(unique_topics[i:i+4]) + "\n"
            
        return formatted_topics.strip() if formatted_topics else "#MARKET_STABLE_NOW"
    except Exception as e:
        return f"#ANALYSIS_ERROR_{datetime.now().second}"

def make_report():
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    msg = f"📊 *Daily Market Intelligence ({now})*\n"
    msg += " " + "="*23 + "\n"
    
    # 1. 지수 정보
    indices = {"KOSPI": "^KS11", "KOSPI 200": "^KS200", "KOSDAQ": "^KQ11", "S&P 500": "^GSPC", "NASDAQ": "^IXIC"}
    msg = f"📊 *Daily Stocks Briefing ({now})*\n"
    if us_status: msg += f" {us_status}\n"
    msg += " " + "="*23 + "\n"
    for name, ticker in indices.items():
        val, rate, mark = get_stock_info(ticker)
        msg += f"• *{name:.<10}*: {val} ({mark}{rate})\n"

    # 2. 🔥 주제 중심 트렌드 (강화된 버전)
    msg += "\n📰 *HOT TOPICS CLOUD*\n"
    msg += f"```\n{get_market_topics()}\n```\n"

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

    for name, ticker in stocks:
        try:
            d = yf.Ticker(ticker).history(period="2d", timeout=5)
            chg = ((d['Close'].iloc[-1] - d['Close'].iloc[-2]) / d['Close'].iloc[-2]) * 100
            icon = "🔴" if chg > 0 else "🔵" if chg < 0 else "⚪"
            msg += f"{icon} {name} ({chg:+.2f}%)\n"
        except: continue

    msg += "\n" + "="*25
    return msg

def send_telegram():
    if not TOKEN or not CHAT_ID: return
    try:
        report = make_report()
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                      json={"chat_id": CHAT_ID, "text": report, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    send_telegram()
