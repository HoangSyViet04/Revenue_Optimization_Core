import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pandas as pd
import numpy as np
from src.database.connection import get_db_engine

def load_sales_data():
    """
    (GIỮ NGUYÊN) Load dữ liệu từ SQL Server.
    """
    engine = get_db_engine()
    query = """
    SELECT 
        CAST(o.OrderDate AS DATE) as Date,
        oi.ProductID,
        p.CategoryID,
        AVG(oi.SellingPrice) as AvgPrice,
        COUNT(oi.ProductID) as QuantitySold,
        MAX(p.CurrentStock) as CurrentStock
    FROM OrderItems oi
    JOIN Orders o ON oi.OrderID = o.OrderID
    JOIN Products p ON oi.ProductID = p.ProductID
    WHERE o.OrderStatus = 'delivered'
    GROUP BY CAST(o.OrderDate AS DATE), oi.ProductID, p.CategoryID
    ORDER BY oi.ProductID, Date
    """
    print("Đang tải dữ liệu từ SQL Server...")
    df = pd.read_sql(query, engine)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def generate_features(df):
    print("Đang tính toán Features...")
    
    # Sắp xếp quan trọng để tính toán theo thời gian
    df = df.sort_values(by=['ProductID', 'Date'])

    # 1. NHÓM SEASONALITY (Mùa vụ)
    df['DayOfWeek'] = df['Date'].dt.dayofweek # <--- CŨ
    df['IsWeekend'] = df['DayOfWeek'].apply(lambda x: 1 if x >= 5 else 0) # <--- CŨ
    
    # [MỚI THÊM] Tháng và Quý
    df['Month'] = df['Date'].dt.month
    df['Quarter'] = df['Date'].dt.quarter
    
    # 2. NHÓM TREND (Xu hướng bán hàng)
    # Sức bán trung bình 7 ngày
    df['Rolling_Sales_7d'] = df.groupby('ProductID')['QuantitySold'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )
    # Bán hôm qua
    df['Lag_Sales_1d'] = df.groupby('ProductID')['QuantitySold'].shift(1).fillna(0)

    # 3. NHÓM RECENCY & STOCK (Độ mới & Tồn kho)
    # [MỚI THÊM] Days_Since_Last_Sale: Khoảng cách ngày giữa 2 lần bán
    df['Days_Since_Last_Sale'] = df.groupby('ProductID')['Date'].diff().dt.days.fillna(0)
    
    #  Áp lực tồn kho (Stock / Sức bán)
    df['Days_To_Stockout'] = df['CurrentStock'] / (df['Rolling_Sales_7d'] + 0.1)

    # 4. NHÓM ELASTICITY (Độ co giãn giá) 
    # Tính % thay đổi giá và lượng so với lần trước
    df['Pct_Change_Price'] = df.groupby('ProductID')['AvgPrice'].pct_change()
    df['Pct_Change_Qty'] = df.groupby('ProductID')['QuantitySold'].pct_change()
    
    # Elasticity = %Qty / %Price
    # Nếu giá không đổi (chia cho 0) -> Gán là NaN rồi fill 0
    df['Elasticity'] = df['Pct_Change_Qty'] / df['Pct_Change_Price'].replace(0, np.nan)
    df['Elasticity'] = df['Elasticity'].fillna(0)
    
    # Chặn giá trị ảo để tránh nhiễu model
    df['Elasticity'] = df['Elasticity'].clip(-10, 10)

    # 5. NHÓM MARKET (Thị trường)
    # Giả lập giá đối thủ
    np.random.seed(42)
    df['CompetitorPrice'] = df['AvgPrice'] * np.random.uniform(0.9, 1.1, size=len(df))
    df['Price_Ratio'] = df['AvgPrice'] / df['CompetitorPrice']

    # Dọn dẹp cột rác
    final_df = df.drop(columns=['Pct_Change_Price', 'Pct_Change_Qty'])
    final_df = final_df.fillna(0)
    
    print(f"Đã tạo xong Features! Kích thước dữ liệu cuối cùng: {final_df.shape}")

    final_df.to_csv('D:\\Learn\\RevenueCore\\data.csv', index=False)
    return final_df

if __name__ == "__main__":
    data = load_sales_data()
    features = generate_features(data)

    cols_to_check = [
        'Date', 'ProductID', 'QuantitySold', 'AvgPrice', 
        'CompetitorPrice', 'Price_Ratio', 
        'Elasticity', 'Days_Since_Last_Sale', 
        'Month', 'Days_To_Stockout'
    ]
    
    print("\n--- CHECK KẾT QUẢ : ---")
    # Dùng to_string() để in ra hết không bị dấu ...
    print(features.tail(10).to_string())