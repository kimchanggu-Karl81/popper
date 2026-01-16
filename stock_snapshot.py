import yfinance as yf
import pandas as pd
import requests
import os
from datetime import datetime

# 환경 변수 설정
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

def get_market_data():
    now = datetime.now().strftime('%Y%m%d')
    filename = f"Daily_Stock_Report_{now}.xlsx"
    
    # [1] 업종별 지수 수익률 데이터 (예시 수치 및 yfinance 활용)
    # 실제 지수 티커가 있다면 yf.download를 사용하세요.
    sector_indices = {
        "전기전자": "+3.10%", "의약품": "+3.25%", "금융": "+2.40%", 
        "운수장비": "+1.85%", "건설": "+1.15%", "화학": "+0.15%", "철강금속": "-0.85%"
    }
    df_sectors = pd.DataFrame(list(sector_indices.items()), columns=['업종명', '1주 수익률'])

    # [2] 업종별 주간 상위 3개 종목 데이터
    stock_data = [
        ["전기전자", "삼성전자(+4.5%)", "SK하이닉스(+3.8%)", "LG엔솔(+2.5%)"],
        ["의약품", "삼성바이오(+5.2%)", "셀트리온(+3.9%)", "유한양행(+2.4%)"],
        ["금융", "KB금융(+4.8%)", "신한지주(+4.1%)", "메리츠금융(+3.2%)"],
        ["운수장비", "현대차(+3.2%)", "기아(+2.8%)", "현대모비스(+1.5%)"]
    ]
    df_stocks = pd.DataFrame(stock_data, columns=['업종', '상위 1위', '상위 2위', '상위 3위'])

    # 엑셀 파일 저장
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df_sectors.to_excel(writer, sheet_name='업종별지수', index=False)
        df_stocks.to_excel(writer, sheet_name='상위종목', index=False)
    
    return filename

def send_excel_to_telegram(filename):
    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"
    with open(filename, 'rb') as f:
        files = {'document': f}
        data = {'chat_id': CHAT_ID, 'caption': f"📅 {datetime.now().strftime('%Y-%m-%d')} 주식 시장 상세 보고서(Excel)입니다."}
        response = requests.post(url, data=data, files=files)
    
    if response.status_code == 200:
        print("엑셀 보고서 전송 성공")
        os.remove(filename) # 전송 후 파일 삭제
    else:
        print(f"전송 실패: {response.text}")

if __name__ == "__main__":
    file = get_market_data()
    send_excel_to_telegram(file)
