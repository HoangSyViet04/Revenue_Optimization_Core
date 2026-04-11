import pandas as pd
import os
from src.config import RAW_DATA_DIR

def extract_data():
    """
    Đọc dữ liệu thô từ file CSV (UK Online Retail II Dataset).
    Gộp 2 file (Year 2009-2010, Year 2010-2011) thành 1 DataFrame.
    """
    print("Đang đọc dữ liệu từ CSV (UK Online Retail II)...")
    
    try:
        df1 = pd.read_csv(os.path.join(RAW_DATA_DIR, 'Year 2009-2010.csv'), encoding='latin1')
        df2 = pd.read_csv(os.path.join(RAW_DATA_DIR, 'Year 2010-2011.csv'), encoding='latin1')
        
        df = pd.concat([df1, df2], ignore_index=True)
        print(f"Đã đọc {len(df):,} dòng dữ liệu thô.")
        
        return {'transactions': df}
        
    except FileNotFoundError as e:
        print(f"Không tìm thấy file dữ liệu: {e}")
        print(f"Hãy chắc chắn bạn đã copy file csv vào: {RAW_DATA_DIR}")
        return None