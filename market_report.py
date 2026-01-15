import yfinance as yf
import pandas as pd
import os
import requests

# 1. 시가총액 상위 주요 티커 리스트 (미국 S&P100 및 한국 KOSPI200 주요 종목)
US_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "TSLA", "UNH", "LLY",
    "JPM", "XOM", "V", "MA", "AVGO", "HD", "PG", "COST", "ORCL", "ADBE"
]

KR_TICKERS = [
    "005930.KS", "000660.KS", "373220.KS", "207940.KS", "005380.KS", 
    "068270.KS", "005490.KS", "051910.KS", "000270.KS", "035420.KS"
]

def get_market_data(tickers):
    results = []
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            if len(hist) >= 2:
                change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                results.append({'ticker': ticker, 'change': change})
        except: continue
    df = pd.DataFrame(results)
    if df.empty: return pd.DataFrame(), pd.DataFrame()
    return df.sort_values(by='change', ascending=False).head(5), df.sort_values(by='change', ascending=True).head(5)

def get_val_summary(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        name = info.get('longName', ticker)
        return (f"📌 <b>{name}</b> ({ticker})\n"
                f"  - PER: {info.get('trailingPE', 'N/A')} / P/S: {info.get('priceToSalesTrailing12Months', 'N/A')}\n"
                f"  - 목표주가: ${info.get('targetMeanPrice', 'N/A')} ({info.get('recommendationKey', 'N/A').upper()})")
    except: return f"⚠️ {ticker}: 분석 실패"

def send_telegram(message):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, data={'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'})

if __name__ == "__main__":
    us_top, us_bottom = get_market_data(US_TICKERS)
    kr_top, kr_bottom = get_market_data(KR_TICKERS)

    msg = "📊 <b>오전 8:30 증시 브리핑</b>\n\n"
    msg += "🇺🇸 <b>미국(S&P100) TOP 5</b>\n"
    msg += "\n".join([f"- {r.ticker}: {r.change:.2f}%" for _, r in us_top.iterrows()]) + "\n\n"
    msg += "🇰🇷 <b>한국(KOSPI200) TOP 5</b>\n"
    msg += "\n".join([f"- {r.ticker}: {r.change:.2f}%" for _, r in kr_top.iterrows()]) + "\n\n"

    msg += "🔍 <b>미국 상위 종목 Valuation</b>\n"
    for t in list(us_top['ticker']):
        msg += "\n" + get_val_summary(t) + "\n"

    send_telegram(msg)
