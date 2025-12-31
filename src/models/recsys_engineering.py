import sys
import os
# Fix đường dẫn
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pandas as pd
from src.database.connection import get_db_engine
from mlxtend.preprocessing import TransactionEncoder

def load_transaction_data(min_product_frequency=50):
    """
    Bước 1: Lấy dữ liệu Giỏ hàng từ SQL.
    Chỉ lấy các sản phẩm xuất hiện ít nhất 'min_product_frequency' lần để giảm nhiễu.
    """
    engine = get_db_engine()
    print("Đang tải dữ liệu giao dịch từ SQL Server...")

    # Query: Lấy OrderID và Tên danh mục sản phẩm (Category)
    # Tại sao dùng Category? Vì Olist có 32k sản phẩm, ma trận sẽ quá lớn -> Dùng Category để gợi ý chung (Vd: Mua Giường -> Gợi ý Gối)
    # Nếu muốn chi tiết hơn thì dùng ProductID, nhưng sẽ cần RAM khủng.
    query = """
    SELECT 
        o.OrderOriginalID,
        c.CategoryNameEN as Item
    FROM OrderItems oi
    JOIN Orders o ON oi.OrderID = o.OrderID
    JOIN Products p ON oi.ProductID = p.ProductID
    JOIN Categories c ON p.CategoryID = c.CategoryID
    WHERE o.OrderStatus = 'delivered'
    """
    df = pd.read_sql(query, engine)
    
    # Loại bỏ các đơn hàng hoặc sản phẩm bị null
    df = df.dropna()
    
    # Lọc bớt các Category quá hiếm (ít người mua) để thuật toán chạy nhanh
    item_counts = df['Item'].value_counts()
    popular_items = item_counts[item_counts >= min_product_frequency].index
    df_filtered = df[df['Item'].isin(popular_items)]
    
    print(f"-> Tổng số dòng dữ liệu: {len(df_filtered)}")
    print(f"-> Số lượng Categories độc nhất: {df_filtered['Item'].nunique()}")

    return df_filtered

def transform_data(df):
    """
    Bước 2: Chuyển đổi sang định dạng One-Hot (Basket Format).
    """
    print("Đang chuyển đổi dữ liệu sang ma trận One-Hot (Basket)...")
    
    # Gom nhóm: Mỗi OrderID sẽ có 1 list các Items
    # Ví dụ: Order_1 -> ['Bed', 'Bath', 'Table']
    transactions = df.groupby('OrderOriginalID')['Item'].apply(list).values.tolist()
    
    # Sử dụng TransactionEncoder để one-hot encode
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_basket = pd.DataFrame(te_ary, columns=te.columns_)
    
    print(f"Đã biến đổi xong! Kích thước ma trận: {df_basket.shape}")
    print("(Hàng là Đơn hàng, Cột là Categories. True=Có mua, False=Không mua)")
    
    return df_basket

if __name__ == "__main__":
    # Test thử
    raw_data = load_transaction_data()
    basket = transform_data(raw_data)
    
    print("\n--- XEM THỬ 5 DÒNG CỦA MA TRẬN BASKET ---")
    print(basket.head().iloc[:, :5]) # Chỉ in 5 cột đầu tiên cho gọn