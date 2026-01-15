import yfinance as yf
import pandas as pd
import os
import requests

# 1. 대상 티커 리스트 (분석 대상을 상위 30개 정도로 넓혀야 상위 10개를 뽑기 수월합니다)
US_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "TSLA", "UNH", "LLY",
    "JPM", "XOM", "V", "MA", "AVGO", "HD", "PG", "COST", "ORCL", "ADBE",
    "ASML", "CVX", "KO", "PEP", "ABBV", "MRK", "CRM", "BAC", "WMT", "ACN"
]

KR_TICKERS = [
    "005930.KS", "000660.KS", "373220.KS", "207940.KS", "005380.KS", 
    "068270.KS", "005490.KS", "051910.KS", "000270.KS", "035420.KS",
    "006400.KS", "000810.KS", "012330.KS", "066570.KS", "032830.KS"
]

def get_market_data(tickers):
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            name = stock.info.get('shortName', ticker)
            
            if len(hist) >= 2:
                change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                results.append({'ticker': ticker, 'name': name, 'change': change})
        except: continue
    df = pd.DataFrame(results)
    if df.empty: return pd.DataFrame()
    
    # 수익률 기준 내림차순 정렬 (상위 종목들이 위로 오게 함)
    return df.sort_values(by='change', ascending=False)

def get_val_summary(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        name = info.get('shortName', ticker)
        
        # 수치 반올림 및 N/A 처리
        per = info.get('trailingPE', 'N/A')
        if isinstance(per, (int, float)): per = round(per, 2)
        
        ps = info.get('priceToSalesTrailing12Months', 'N/A')
        if isinstance(ps, (int, float)): ps = round(ps, 2)

        target = info.get('targetMeanPrice', 'N/A')
        recommend = info.get('recommendationKey', 'N/A').upper()

        return (f"📌 <b>{name}</b> ({ticker})\n"
                f"  - PER: {per} / P/S: {ps}\n"
                f"  - 목표주가: ${target} ({recommend})")
    except: return f"⚠️ {ticker}: 분석 실패"

def send_telegram(message):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    # 메시지가 너무 길면 텔레그램에서 거부될 수 있으므로 분할 전송 로직 추가
    if len(message) > 4000:
        for i in range(0, len(message), 4000):
            requests.post(url, data={'chat_id': chat_id, 'text': message[i:i+4000], 'parse_mode': 'HTML'})
    else:
        requests.post(url, data={'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'})

if __name__ == "__main__":
    us_data = get_market_data(US_TICKERS)
    kr_data = get_market_data(KR_TICKERS)

    msg = "📊 <b>오전 8:30 증시 브리핑 (확장 리포트)</b>\n\n"
    
    msg += "🇺🇸 <b>미국(S&P) 수익률 상위</b>\n"
    msg += "\n".join([f"- {r['name']} ({r['ticker']}): {r['change']:.2f}%" for _, r in us_data.head(5).iterrows()]) + "\n\n"
    
    msg += "🇰🇷 <b>한국(KOSPI) 수익률 상위</b>\n"
    msg += "\n".join([f"- {r['name']} ({r['ticker']}): {r['change']:.2f}%" for _, r in kr_data.head(5).iterrows()]) + "\n\n"

    # Valuation 대상을 상위 10개로 확장 (미국 상위 10개 예시)
    msg += "🔍 <b>수익률 상위 10개 종목 Valuation</b>\n"
    top_10_list = list(us_data.head(10)['ticker'])
    
    for t in top_10_list:
        msg += "\n" + get_val_summary(t) + "\n"

    send_telegram(msg)
