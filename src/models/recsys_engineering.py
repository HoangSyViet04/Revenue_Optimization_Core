import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pandas as pd
from src.database.connection import get_db_engine
from mlxtend.preprocessing import TransactionEncoder

def load_transaction_data(min_product_frequency=30):
    """
    Bước 1: Lấy dữ liệu giỏ hàng từ SQL.
    Dùng Description (tên sản phẩm) vì UK Retail có ~20 items/order → đủ dày cho FP-Growth.
    Chỉ lấy sản phẩm xuất hiện ít nhất 'min_product_frequency' lần để giảm nhiễu.
    """
    engine = get_db_engine()
    print("Đang tải dữ liệu giao dịch từ SQL Server...")

    query = """
    SELECT 
        o.InvoiceNo,
        p.Description as Item
    FROM OrderItems oi
    JOIN Orders o ON oi.OrderID = o.OrderID
    JOIN Products p ON oi.ProductID = p.ProductID
    WHERE p.Description IS NOT NULL
    """
    df = pd.read_sql(query, engine)
    df = df.dropna()
    
    # Lọc bớt sản phẩm quá hiếm
    item_counts = df['Item'].value_counts()
    popular_items = item_counts[item_counts >= min_product_frequency].index
    df_filtered = df[df['Item'].isin(popular_items)]
    
    print(f"-> Tổng số dòng dữ liệu: {len(df_filtered)}")
    print(f"-> Số lượng Products độc nhất: {df_filtered['Item'].nunique()}")

    return df_filtered

def transform_data(df):
    """
    Bước 2: Chuyển đổi sang định dạng One-Hot (Basket Format).
    """
    print("Đang chuyển đổi dữ liệu sang ma trận One-Hot (Basket)...")
    
    # Gom nhóm: Mỗi InvoiceNo sẽ có 1 list các Items
    transactions = df.groupby('InvoiceNo')['Item'].apply(list).values.tolist()
    
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_basket = pd.DataFrame(te_ary, columns=te.columns_)
    
    print(f"Đã biến đổi xong! Kích thước ma trận: {df_basket.shape}")
    print("(Hàng là Đơn hàng, Cột là Products. True=Có mua, False=Không mua)")
    
    return df_basket

if __name__ == "__main__":
    raw_data = load_transaction_data()
    basket = transform_data(raw_data)
    
    print("\n--- XEM THỬ 5 DÒNG CỦA MA TRẬN BASKET ---")
    print(basket.head().iloc[:, :5])