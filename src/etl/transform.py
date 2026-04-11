import pandas as pd
import numpy as np

def transform_data(raw_data):
    """
    Nhận vào dict raw_data (từ bước Extract), thực hiện:
    1. Lọc giao dịch hợp lệ (bỏ đơn hủy, quantity âm, thiếu Customer ID).
    2. Tạo bảng Products, Customers, Orders, OrderItems chuẩn hóa.
    """
    print("Đang xử lý và làm sạch dữ liệu (Transform)...")
    
    df = raw_data['transactions'].copy()
    
    # --- 1. LÀM SẠCH DỮ LIỆU ---
    # Bỏ đơn hủy (Invoice bắt đầu bằng 'C')
    df['Invoice'] = df['Invoice'].astype(str)
    df = df[~df['Invoice'].str.startswith('C')]
    
    # Bỏ Quantity <= 0, Price <= 0, thiếu Customer ID
    df = df[(df['Quantity'] > 0) & (df['Price'] > 0) & (df['Customer ID'].notna())]
    
    # Bỏ StockCode không phải sản phẩm thật (POST, DOT, M, BANK CHARGES, etc.)
    non_product_codes = ['POST', 'DOT', 'M', 'BANK CHARGES', 'PADS', 'CRUK', 'C2', 'D']
    df = df[~df['StockCode'].isin(non_product_codes)]
    
    # Bỏ Description null
    df = df.dropna(subset=['Description'])
    
    # Chuẩn hóa
    df['Customer ID'] = df['Customer ID'].astype(int).astype(str)
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['Description'] = df['Description'].str.strip().str.upper()
    
    print(f"  Sau khi lọc: {len(df):,} giao dịch hợp lệ")
    
    # --- 2. TẠO BẢNG PRODUCTS ---
    # Mỗi StockCode lấy Description xuất hiện nhiều nhất (mode)
    product_desc = df.groupby('StockCode')['Description'].agg(lambda x: x.mode().iloc[0]).reset_index()
    # Giá cơ sở = median price (ổn định hơn mean, tránh outlier)
    product_price = df.groupby('StockCode')['Price'].median().reset_index()
    product_price.columns = ['StockCode', 'BasePrice']
    
    df_products = product_desc.merge(product_price, on='StockCode')
    # Tồn kho giả lập dựa trên số lượng bán (realistic hơn random)
    product_qty = df.groupby('StockCode')['Quantity'].sum().reset_index()
    product_qty.columns = ['StockCode', 'TotalSold']
    df_products = df_products.merge(product_qty, on='StockCode')
    # Stock = tỷ lệ theo tổng bán (giả lập có hàng tồn kho)
    np.random.seed(42)
    df_products['CurrentStock'] = (df_products['TotalSold'] * np.random.uniform(0.1, 0.5, len(df_products))).astype(int)
    df_products = df_products[['StockCode', 'Description', 'BasePrice', 'CurrentStock']]
    
    # --- 3. TẠO BẢNG CUSTOMERS ---
    df_customers = df[['Customer ID', 'Country']].drop_duplicates(subset=['Customer ID'])
    df_customers.columns = ['CustomerOriginalID', 'Country']
    
    # --- 4. TẠO BẢNG ORDERS ---
    # Tính tổng tiền mỗi đơn hàng
    order_totals = df.groupby('Invoice').agg(
        TotalAmount=('Price', lambda x: (x * df.loc[x.index, 'Quantity']).sum()),
        OrderDate=('InvoiceDate', 'first'),
        CustomerOriginalID=('Customer ID', 'first')
    ).reset_index()
    order_totals.columns = ['InvoiceNo', 'TotalAmount', 'OrderDate', 'CustomerOriginalID']
    df_orders = order_totals
    
    # --- 5. TẠO BẢNG ORDER ITEMS ---
    # Gom nhóm theo Invoice + StockCode (trường hợp cùng SP xuất hiện nhiều dòng)
    df_items = df.groupby(['Invoice', 'StockCode']).agg(
        Quantity=('Quantity', 'sum'),
        UnitPrice=('Price', 'mean')
    ).reset_index()
    df_items.columns = ['InvoiceNo', 'StockCode', 'Quantity', 'UnitPrice']

    print("Transform hoàn tất!")
    print(f"  Products: {len(df_products):,}")
    print(f"  Customers: {len(df_customers):,}")
    print(f"  Orders: {len(df_orders):,}")
    print(f"  OrderItems: {len(df_items):,}")
    
    return {
        'products': df_products,
        'customers': df_customers,
        'orders': df_orders,
        'items': df_items
    }