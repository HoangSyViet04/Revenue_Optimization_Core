from src.etl.extract import extract_data
from src.etl.transform import transform_data
from src.etl.load import load_data_to_sql
import time

def main():
    start_time = time.time()
    print("BẮT ĐẦU ETL PIPELINE...")
    
    # 1. Extract
    raw_data = extract_data()
    if not raw_data:
        return

    # 2. Transform
    transformed_data = transform_data(raw_data)

    # 3. Load
    load_data_to_sql(transformed_data)
    
    end_time = time.time()
    print(f"XONG! Tổng thời gian chạy: {round(end_time - start_time, 2)} giây.")

if __name__ == "__main__":
    main()