import sys
import os

# Thêm đường dẫn để import được src.config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from sqlalchemy import create_engine, text
from src.config import Config

def create_schema():
    print("Đang kết nối SQL Server để tạo bảng...")
    
    # Lấy connection string từ file config xịn xò
    conn_str = Config.get_connection_string()
    engine = create_engine(conn_str)

    # SQL Script cho UK Online Retail II dataset
    sql_script = """
    -- 1. Dọn dẹp bảng cũ (Thứ tự xóa: Con trước, Cha sau)
    IF OBJECT_ID('OrderItems', 'U') IS NOT NULL DROP TABLE OrderItems;
    IF OBJECT_ID('Orders', 'U') IS NOT NULL DROP TABLE Orders;
    IF OBJECT_ID('Products', 'U') IS NOT NULL DROP TABLE Products;
    IF OBJECT_ID('Customers', 'U') IS NOT NULL DROP TABLE Customers;

    -- 2. Bảng Customers
    CREATE TABLE Customers (
        CustomerID INT PRIMARY KEY IDENTITY(1,1),
        CustomerOriginalID NVARCHAR(50) NOT NULL, -- Customer ID gốc từ dataset
        Country NVARCHAR(100)
    );

    -- 3. Bảng Products
    CREATE TABLE Products (
        ProductID INT PRIMARY KEY IDENTITY(1,1),
        StockCode NVARCHAR(50) NOT NULL,     -- Mã sản phẩm gốc
        Description NVARCHAR(255),            -- Tên sản phẩm
        BasePrice FLOAT,                      -- Giá trung vị (median) làm giá cơ sở
        CurrentStock INT DEFAULT 0
    );

    -- 4. Bảng Orders
    CREATE TABLE Orders (
        OrderID INT PRIMARY KEY IDENTITY(1,1),
        InvoiceNo NVARCHAR(50),              -- Số hóa đơn gốc
        CustomerID INT,
        OrderDate DATETIME,
        TotalAmount FLOAT,
        FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
    );

    -- 5. Bảng OrderItems
    CREATE TABLE OrderItems (
        OrderItemID INT PRIMARY KEY IDENTITY(1,1),
        OrderID INT,
        ProductID INT,
        Quantity INT DEFAULT 1,
        UnitPrice FLOAT,                     -- Giá bán thực tế lúc mua
        FOREIGN KEY (OrderID) REFERENCES Orders(OrderID),
        FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
    );
    """
    
    try:
        with engine.begin() as conn:
            conn.execute(text(sql_script))
        print("Đã tạo Schema thành công!")
    except Exception as e:
        print(f"Lỗi tạo bảng: {e}")

if __name__ == "__main__":
    create_schema()

    