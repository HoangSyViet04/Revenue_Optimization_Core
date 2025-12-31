import pandas as pd
from src.database.connection import get_db_engine
from sqlalchemy import text

def load_data_to_sql(transformed_data):
    engine = get_db_engine()
    
    # Lấy data đã làm sạch
    df_cats = transformed_data['categories']
    df_prods = transformed_data['products']
    df_custs = transformed_data['customers']
    df_orders = transformed_data['orders']
    df_items = transformed_data['items']

    print("Bắt đầu nạp dữ liệu vào SQL Server (Bulk Insert)...")

    with engine.begin() as conn:
        # 1. Load Categories
        print(f"-> Loading {len(df_cats)} Categories...")
        df_cats.to_sql('Categories', conn, if_exists='append', index=False)
        
        # --- MAPPING CATEGORY ID ---
        # Lấy lại ID vừa sinh ra từ SQL để gán cho Products
        map_cats = pd.read_sql("SELECT CategoryID, CategoryNameEN FROM Categories", conn)
        # Tạo từ điển: {'Electronics': 1, 'Toys': 2...}
        cat_dict = dict(zip(map_cats['CategoryNameEN'], map_cats['CategoryID']))
        
        # Map vào bảng Products
        df_prods['CategoryID'] = df_prods['CategoryNameEN'].map(cat_dict)
        # Bỏ cột tên đi, chỉ giữ ID
        df_prods_load = df_prods[['ProductOriginalID', 'CategoryID', 'OriginalPrice', 'CurrentStock']]
        
        # 2. Load Products
        print(f"-> Loading {len(df_prods_load)} Products...")
        df_prods_load.to_sql('Products', conn, if_exists='append', index=False)

        # 3. Load Customers
        print(f"-> Loading {len(df_custs)} Customers...")
        df_custs_load = df_custs[['CustomerUniqueID', 'RealUniqueID', 'CustomerCity', 'CustomerState']]
        df_custs_load.to_sql('Customers', conn, if_exists='append', index=False)

        # --- MAPPING CUSTOMER ID ---
        print("-> Mapping Customer IDs ...")
        # Chỉ lấy 2 cột cần thiết để map
        map_cust = pd.read_sql("SELECT CustomerID, CustomerUniqueID FROM Customers", conn)
        cust_dict = dict(zip(map_cust['CustomerUniqueID'], map_cust['CustomerID']))
        
        # Map vào bảng Orders
        df_orders['CustomerID'] = df_orders['CustomerUniqueID'].map(cust_dict)
        # Lọc bỏ đơn hàng nào không tìm thấy khách (Data rác)
        df_orders = df_orders.dropna(subset=['CustomerID'])
        
        # 4. Load Orders
        print(f"-> Loading {len(df_orders)} Orders...")
        # THÊM 'TotalAmount' VÀO DANH SÁCH CỘT DƯỚI ĐÂY
        df_orders_load = df_orders[['OrderOriginalID', 'CustomerID', 'OrderDate', 'OrderStatus', 'TotalAmount']]
        df_orders_load.to_sql('Orders', conn, if_exists='append', index=False)

        # --- MAPPING ORDER ID & PRODUCT ID CHO ORDER ITEMS ---
        print("-> Mapping OrderItems...")
        
        # Lấy Map Product (Vừa insert ở bước 2)
        map_prod = pd.read_sql("SELECT ProductID, ProductOriginalID FROM Products", conn)
        prod_dict = dict(zip(map_prod['ProductOriginalID'], map_prod['ProductID']))
        
        # Lấy Map Order (Vừa insert ở bước 4)
        # Lưu ý: Vì bảng Orders lớn, nên query khéo léo hoặc chấp nhận chờ xíu
        map_ord = pd.read_sql("SELECT OrderID, OrderOriginalID FROM Orders", conn)
        ord_dict = dict(zip(map_ord['OrderOriginalID'], map_ord['OrderID']))
        
        # Map cả 2 vào Items
        df_items['OrderID'] = df_items['OrderOriginalID'].map(ord_dict)
        df_items['ProductID'] = df_items['ProductOriginalID'].map(prod_dict)
        
        # Bỏ dòng null (rác)
        df_items = df_items.dropna(subset=['OrderID', 'ProductID'])
        
        # 5. Load OrderItems
        print(f"-> Loading {len(df_items)} OrderItems...")
        df_items_load = df_items[['OrderID', 'ProductID', 'Quantity', 'SellingPrice', 'FreightValue']]
        # chunksize giúp chia nhỏ ra để insert đỡ bị đơ máy
        df_items_load.to_sql('OrderItems', conn, if_exists='append', index=False, chunksize=1000)

    print("HOÀN TẤT TOÀN BỘ QUÁ TRÌNH LOAD DỮ LIỆU!")