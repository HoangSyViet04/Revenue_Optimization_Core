import pandas as pd
import numpy as np

def transform_data(raw_data):
    """
    Nhận vào dict raw_data (từ bước Extract), thực hiện:
    1. Merge bản dịch category.
    2. Giả lập tồn kho (Inventory Simulation).
    3. Làm sạch kiểu dữ liệu.
    """
    print("Đang xử lý và giả lập dữ liệu (Transform)...")
    
    orders = raw_data['orders']
    items = raw_data['items']
    products = raw_data['products']
    translations = raw_data['translations']
    customers = raw_data['customers']

    # --- 1. XỬ LÝ CATEGORIES & PRODUCTS ---
    # Merge tên tiếng Anh vào
    products = products.merge(translations, on='product_category_name', how='left')
    products['product_category_name_english'] = products['product_category_name_english'].fillna('Unknown')
    
    # Tạo bảng Categories duy nhất
    df_categories = products[['product_category_name', 'product_category_name_english']].drop_duplicates()
    df_categories.columns = ['CategoryNameOriginal', 'CategoryNameEN']
    
    # Giả lập Tồn kho & Giá gốc cho Products
    # Logic: Giá gốc cao hơn giá bán trung bình 1 xíu. Tồn kho random.
    products['CurrentStock'] = np.random.randint(0, 100, size=len(products))
    products['OriginalPrice'] = 0.0 # Tạm thời để 0, logic phức tạp tính sau
    
    # Đổi tên cột cho khớp với SQL
    df_products = products[['product_id', 'product_category_name_english', 'CurrentStock', 'OriginalPrice']]
    df_products.columns = ['ProductOriginalID', 'CategoryNameEN', 'CurrentStock', 'OriginalPrice']

    # --- 2. XỬ LÝ CUSTOMERS ---
    df_customers = customers[['customer_id', 'customer_city', 'customer_state', 'customer_unique_id']]
    # customer_id trong Olist thực ra là transaction-level id, unique_id mới là user thật
    # Tuy nhiên để đơn giản bước đầu, ta dùng customer_id làm ID đại diện
    df_customers.columns = ['CustomerUniqueID', 'CustomerCity', 'CustomerState', 'RealUniqueID']
    df_customers = df_customers.drop_duplicates(subset=['CustomerUniqueID'])

    # --- 3. XỬ LÝ ORDERS ---
    # Bước 3.1: Tính tổng tiền từng đơn từ bảng Items gốc
    # Group by order_id và cộng dồn price + freight
    order_sums = items.groupby('order_id')[['price', 'freight_value']].sum().reset_index()
    order_sums['TotalAmount'] = order_sums['price'] + order_sums['freight_value']
    
    # Bước 3.2: Merge vào bảng Orders
    df_orders = orders.merge(order_sums[['order_id', 'TotalAmount']], on='order_id', how='left')
    
    # Fill 0 cho những đơn không có item (tránh lỗi NaN)
    df_orders['TotalAmount'] = df_orders['TotalAmount'].fillna(0.0)

    # Bước 3.3: Chuẩn hóa cột
    df_orders = df_orders[['order_id', 'customer_id', 'order_purchase_timestamp', 'order_status', 'TotalAmount']]
    df_orders.columns = ['OrderOriginalID', 'CustomerUniqueID', 'OrderDate', 'OrderStatus', 'TotalAmount']
    df_orders['OrderDate'] = pd.to_datetime(df_orders['OrderDate'])
    
    # --- 4. XỬ LÝ ORDER ITEMS ---
    df_items = items[['order_id', 'product_id', 'order_item_id', 'price', 'freight_value']]
    df_items.columns = ['OrderOriginalID', 'ProductOriginalID', 'Quantity', 'SellingPrice', 'FreightValue']
    # Quantity trong Olist bị tách dòng, ta gom lại (Group by)
    df_items = df_items.groupby(['OrderOriginalID', 'ProductOriginalID']).agg({
        'Quantity': 'count', # Đếm số dòng thành số lượng
        'SellingPrice': 'mean',
        'FreightValue': 'sum'
    }).reset_index()

    print("Transform hoàn tất!")
    
    return {
        'categories': df_categories,
        'products': df_products,
        'customers': df_customers,
        'orders': df_orders,
        'items': df_items
    }