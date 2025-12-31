import pandas as pd
import os
from src.config import RAW_DATA_DIR

def extract_data():
    """
    Đọc dữ liệu thô từ file CSV (Olist Dataset).
    Trả về một dictionary chứa các DataFrames.
    """
    print("Đang đọc dữ liệu từ CSV...")
    
    try:
        # 1. Đọc Orders
        orders = pd.read_csv(os.path.join(RAW_DATA_DIR, 'olist_orders_dataset.csv'))
        
        # 2. Đọc Order Items (Chi tiết đơn hàng)
        items = pd.read_csv(os.path.join(RAW_DATA_DIR, 'olist_order_items_dataset.csv'))
        
        # 3. Đọc Products
        products = pd.read_csv(os.path.join(RAW_DATA_DIR, 'olist_products_dataset.csv'))
        
        # 4. Đọc Category Translation (Để dịch tên danh mục)
        translations = pd.read_csv(os.path.join(RAW_DATA_DIR, 'product_category_name_translation.csv'))
        
        # 5. Đọc Customers
        customers = pd.read_csv(os.path.join(RAW_DATA_DIR, 'olist_customers_dataset.csv'))

        print("Extract dữ liệu thành công!")
        
        # Đóng gói vào dict để dễ truyền sang bước Transform
        return {
            'orders': orders,
            'items': items,
            'products': products,
            'translations': translations,
            'customers': customers
        }
        
    except FileNotFoundError as e:
        print(f"Không tìm thấy file dữ liệu: {e}")
        print(f"Hãy chắc chắn bạn đã copy file csv vào: {RAW_DATA_DIR}")
        return None