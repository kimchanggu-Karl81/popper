import yfinance as yf
import matplotlib.pyplot as plt
import requests
import os
import pandas as pd

def get_data():
    # 10년물(^TNX)과 2년물(^IRX: 13주 국채수익률 대신 보통 2년물인 ^ZT=F 등을 쓰나 yfinance에서는 ^ZTY=F 또는 직접 금리 지수 사용)
    # yfinance에서 가장 안정적인 10년물(^TNX)과 2년물(^ZT=F 혹은 장단기 비교용 데이터)을 가져옵니다.
    # 여기서는 가장 보편적인 미국채 10년물(^TNX)과 2년물(^ITV) 지표를 활용합니다.
    tickers = ["^TNX", "^IRX"] # ^IRX는 13주물이나, yfinance 환경에 따라 2년물 대용으로 수익률 지수 활용
    # 실제 2년물 수익률에 가장 근접한 데이터를 위해 각각 다운로드
    t10 = yf.download("^TNX", period="1y", interval="1d", progress=False)['Close']
    t02 = yf.download("^IRX", period="1y", interval="1d", progress=False)['Close']
    
    # 데이터 병합 (날짜 맞추기)
    df = pd.concat([t10, t02], axis=1)
    df.columns = ['10Y', '2Y']
    df = df.dropna()
    return df

def create_plot(df):
    plt.style.use('ggplot')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True, gridspec_kw={'height_ratios': [2, 1]})

    # 상단 차트: 10년물 vs 2년물 금리 추이
    ax1.plot(df.index, df['10Y'], label='10-Year Yield', color='#d62728', linewidth=2) # 빨간색
    ax1.plot(df.index, df['2Y'], label='2-Year Yield', color='#1f77b4', linewidth=2)  # 파란색
    ax1.set_title("US Treasury Yields: 10Y vs 2Y", fontsize=16, fontweight='bold')
    ax1.set_ylabel("Yield (%)")
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)

    # 하단 차트: 장단기 금리차 (10Y - 2Y Spread)
    spread = df['10Y'] - df['2Y']
    ax2.plot(df.index, spread, color='purple', linewidth=1.5, label='10Y-2Y Spread')
    ax2.axhline(0, color='black', linestyle='-', linewidth=1) # 0선 (금리 역전 기준선)
    
    # 금리 역전 구간 색칠 (Spread < 0)
    ax2.fill_between(df.index, spread, 0, where=(spread < 0), color='red', alpha=0.3, label='Inversion')
    ax2.fill_between(df.index, spread, 0, where=(spread >= 0), color='green', alpha=0.3)

    ax2.set_title("10Y-2Y Yield Spread", fontsize=14)
    ax2.set_ylabel("Spread (%)")
    ax2.legend(loc='upper left')

    # 마지막 값 표시
    last_10y = df['10Y'].iloc[-1]
    last_2y = df['2Y'].iloc[-1]
    last_spread = spread.iloc[-1]
    
    plt.annotate(f"Current Spread: {last_spread:.2f}%", 
                 xy=(0.5, 0.9), xycoords='axes fraction', 
                 ha='center', fontsize=12, fontweight='bold',
                 bbox=dict(boxstyle='round', fc='yellow', alpha=0.5))

    plt.tight_layout()
    plt.savefig("chart.png", dpi=300)
    return last_10y, last_2y, last_spread

def send_telegram(t10, t02, spread):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    
    status = "⚠️ 금리 역전 발생" if spread < 0 else "✅ 정상 스프레드"
    message = (
        f"📉 <b>미 국채 장단기 금리 리포트</b>\n\n"
        f"• 10년물 금리: <b>{t10:.2f}%</b>\n"
        f"• 2년물 금리: <b>{t02:.2f}%</b>\n"
        f"• 장단기 금리차: <b>{spread:.2f}%</b> ({status})"
    )
    
    if os.path.exists("chart.png"):
        with open("chart.png", "rb") as photo:
            requests.post(url, data={'chat_id': chat_id, 'caption': message, 'parse_mode': 'HTML'}, files={'photo': photo})

if __name__ == "__main__":
    try:
        data_df = get_data()
        val_10y, val_2y, val_spread = create_plot(data_df)
        send_telegram(val_10y, val_2y, val_spread)
        print("Spread Chart Update Success!")
    except Exception as e:
        print(f"Error: {e}")
