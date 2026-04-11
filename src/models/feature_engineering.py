import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pandas as pd
import numpy as np
from src.database.connection import get_db_engine

def load_sales_data():
    """
    Load dữ liệu bán hàng tổng hợp theo ngày + sản phẩm từ SQL Server.
    """
    engine = get_db_engine()
    query = """
    SELECT 
        CAST(o.OrderDate AS DATE) as Date,
        oi.ProductID,
        AVG(oi.UnitPrice) as AvgPrice,
        SUM(oi.Quantity) as QuantitySold,
        MAX(p.CurrentStock) as CurrentStock,
        MAX(p.BasePrice) as BasePrice
    FROM OrderItems oi
    JOIN Orders o ON oi.OrderID = o.OrderID
    JOIN Products p ON oi.ProductID = p.ProductID
    GROUP BY CAST(o.OrderDate AS DATE), oi.ProductID
    ORDER BY oi.ProductID, Date
    """
    print("Đang tải dữ liệu từ SQL Server...")
    df = pd.read_sql(query, engine)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

def generate_features(df):
    print("Đang tính toán Features...")
    
    df = df.sort_values(by=['ProductID', 'Date'])

    # 1. NHÓM SEASONALITY (Mùa vụ)
    df['DayOfWeek'] = df['Date'].dt.dayofweek
    df['IsWeekend'] = df['DayOfWeek'].apply(lambda x: 1 if x >= 5 else 0)
    df['Month'] = df['Date'].dt.month
    df['Quarter'] = df['Date'].dt.quarter
    
    # 2. NHÓM TREND (Xu hướng bán hàng)
    df['Rolling_Sales_7d'] = df.groupby('ProductID')['QuantitySold'].transform(
        lambda x: x.rolling(window=7, min_periods=1).mean()
    )
    df['Lag_Sales_1d'] = df.groupby('ProductID')['QuantitySold'].shift(1).fillna(0)

    # 3. NHÓM RECENCY & STOCK
    df['Days_Since_Last_Sale'] = df.groupby('ProductID')['Date'].diff().dt.days.fillna(0)
    df['Days_To_Stockout'] = df['CurrentStock'] / (df['Rolling_Sales_7d'] + 0.1)

    # 4. NHÓM ELASTICITY (Độ co giãn giá) - Dữ liệu thật từ UK Retail
    df['Pct_Change_Price'] = df.groupby('ProductID')['AvgPrice'].pct_change()
    df['Pct_Change_Qty'] = df.groupby('ProductID')['QuantitySold'].pct_change()
    df['Elasticity'] = df['Pct_Change_Qty'] / df['Pct_Change_Price'].replace(0, np.nan)
    df['Elasticity'] = df['Elasticity'].fillna(0).clip(-10, 10)

    # 5. NHÓM MARKET (Thị trường)
    # Giá đối thủ = Giá trung vị của category (dùng BasePrice làm benchmark)
    # Thực tế hơn random: so sánh giá bán hiện tại với giá cơ sở
    df['CompetitorPrice'] = df['BasePrice']
    df['Price_Ratio'] = df['AvgPrice'] / (df['CompetitorPrice'] + 0.01)

    # Dọn dẹp
    final_df = df.drop(columns=['Pct_Change_Price', 'Pct_Change_Qty', 'BasePrice'])
    final_df = final_df.fillna(0)
    
    print(f"Đã tạo xong Features! Kích thước dữ liệu cuối cùng: {final_df.shape}")
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
    print(features.tail(10).to_string())