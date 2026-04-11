import pandas as pd
from src.database.connection import get_db_engine
from sqlalchemy import text

def load_data_to_sql(transformed_data):
    engine = get_db_engine()
    
    df_prods = transformed_data['products']
    df_custs = transformed_data['customers']
    df_orders = transformed_data['orders']
    df_items = transformed_data['items']

    print("Bắt đầu nạp dữ liệu vào SQL Server (Bulk Insert)...")

    with engine.begin() as conn:
        # 1. Load Customers
        print(f"-> Loading {len(df_custs)} Customers...")
        df_custs.to_sql('Customers', conn, if_exists='append', index=False)
        
        # 2. Load Products
        print(f"-> Loading {len(df_prods)} Products...")
        df_prods.to_sql('Products', conn, if_exists='append', index=False)

        # --- MAPPING IDs ---
        # Lấy lại ID vừa sinh ra từ SQL để map FK
        print("-> Mapping IDs...")
        
        map_cust = pd.read_sql("SELECT CustomerID, CustomerOriginalID FROM Customers", conn)
        cust_dict = dict(zip(map_cust['CustomerOriginalID'], map_cust['CustomerID']))
        
        map_prod = pd.read_sql("SELECT ProductID, StockCode FROM Products", conn)
        prod_dict = dict(zip(map_prod['StockCode'], map_prod['ProductID']))
        
        # 3. Load Orders (map CustomerID)
        df_orders['CustomerID'] = df_orders['CustomerOriginalID'].map(cust_dict)
        df_orders = df_orders.dropna(subset=['CustomerID'])
        df_orders['CustomerID'] = df_orders['CustomerID'].astype(int)
        
        print(f"-> Loading {len(df_orders)} Orders...")
        df_orders_load = df_orders[['InvoiceNo', 'CustomerID', 'OrderDate', 'TotalAmount']]
        df_orders_load.to_sql('Orders', conn, if_exists='append', index=False)

        # Lấy OrderID mapping
        map_ord = pd.read_sql("SELECT OrderID, InvoiceNo FROM Orders", conn)
        ord_dict = dict(zip(map_ord['InvoiceNo'], map_ord['OrderID']))
        
        # 4. Load OrderItems (map OrderID + ProductID)
        df_items['OrderID'] = df_items['InvoiceNo'].map(ord_dict)
        df_items['ProductID'] = df_items['StockCode'].map(prod_dict)
        df_items = df_items.dropna(subset=['OrderID', 'ProductID'])
        df_items['OrderID'] = df_items['OrderID'].astype(int)
        df_items['ProductID'] = df_items['ProductID'].astype(int)
        
        print(f"-> Loading {len(df_items)} OrderItems...")
        df_items_load = df_items[['OrderID', 'ProductID', 'Quantity', 'UnitPrice']]
        df_items_load.to_sql('OrderItems', conn, if_exists='append', index=False, chunksize=1000)

    print("HOÀN TẤT TOÀN BỘ QUÁ TRÌNH LOAD DỮ LIỆU!")