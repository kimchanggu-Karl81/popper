import pandas as pd
import requests
import os
from datetime import datetime

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def create_excel_report():
    now = datetime.now().strftime('%Y-%m-%d')
    file_name = f"Daily_Stocks_Snapshot_{now}.xlsx"
    
    # [1] 업종별 지수 현황 (이미지 양식 기준 전 업종)
    sectors = ["건설", "금융", "운수장비", "유통", "음식료", "의약품", "전기전자", "철강금속", "화학", "유틸리티", "통신"]
    yields = ["+1.15%", "+2.40%", "+1.85%", "+0.55%", "+2.10%", "+3.25%", "+3.10%", "-0.85%", "+0.15%", "+1.20%", "+0.85%"]
    df_indices = pd.DataFrame({"업종명": sectors, "1주 수익률": yields})

    # [2] 업종별 주간 상위 3개 종목 (가독성 위해 3순위까지 포함)
    stock_data = [
        ["전기전자", "삼성전자(+4.5%)", "SK하이닉스(+3.8%)", "LG엔솔(+2.5%)"],
        ["의약품", "삼성바이오(+5.2%)", "셀트리온(+3.9%)", "유한양행(+2.4%)"],
        ["금융", "KB금융(+4.8%)", "신한지주(+4.1%)", "메리츠금융(+3.2%)"],
        ["운수장비", "현대차(+3.2%)", "기아(+2.8%)", "현대모비스(+1.5%)"],
        ["건설", "현대건설(+3.2%)", "대우건설(+2.8%)", "GS건설(+1.5%)"]
    ]
    df_stocks = pd.DataFrame(stock_data, columns=['업종', '상위 1위', '상위 2위', '상위 3위'])

    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        df_indices.to_excel(writer, sheet_name='업종별지수', index=False)
        df_stocks.to_excel(writer, sheet_name='업종별상위종목', index=False)
    
    return file_name

def send_to_telegram(file_name):
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    with open(file_name, 'rb') as f:
        requests.post(url, data={'chat_id': CHAT_ID, 'caption': f"📊 {datetime.now().strftime('%Y-%m-%d')} 상세 엑셀 보고서"}, files={'document': f})
    os.remove(file_name)

if __name__ == "__main__":
    path = create_excel_report()
    send_to_telegram(path)
