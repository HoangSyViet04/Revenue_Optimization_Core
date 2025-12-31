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

    # SQL Script (Đã cập nhật thêm bảng Categories)
    sql_script = """
    -- 1. Dọn dẹp bảng cũ (Thứ tự xóa: Con trước, Cha sau)
    IF OBJECT_ID('OrderItems', 'U') IS NOT NULL DROP TABLE OrderItems;
    IF OBJECT_ID('Orders', 'U') IS NOT NULL DROP TABLE Orders;
    IF OBJECT_ID('Products', 'U') IS NOT NULL DROP TABLE Products;
    IF OBJECT_ID('Categories', 'U') IS NOT NULL DROP TABLE Categories;
    IF OBJECT_ID('Customers', 'U') IS NOT NULL DROP TABLE Customers;

    -- 2. Bảng Categories (Giải quyết vụ Translation)
    CREATE TABLE Categories (
        CategoryID INT PRIMARY KEY IDENTITY(1,1),
        CategoryNameOriginal NVARCHAR(100), -- Tên gốc 
        CategoryNameEN NVARCHAR(100)        -- Tên tiếng Anh (Dùng để hiển thị)
    );

    -- 3. Bảng Customers
    CREATE TABLE Customers (
        CustomerID INT PRIMARY KEY IDENTITY(1,1),
        CustomerUniqueID NVARCHAR(50) NOT NULL, -- ID từ Olist
        RealUniqueID NVARCHAR(50),     -- ID thật của khách (customer_unique_id trong Olist)
        CustomerCity NVARCHAR(100),
        CustomerState NVARCHAR(50)
    );

    -- 4. Bảng Products (Link với Categories)
    CREATE TABLE Products (
        ProductID INT PRIMARY KEY IDENTITY(1,1),
        ProductOriginalID NVARCHAR(50), -- ID gốc từ Olist
        CategoryID INT, 
        OriginalPrice FLOAT, -- Giá cơ sở
        CurrentStock INT DEFAULT 0,
        FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID)
    );

    -- 5. Bảng Orders
    CREATE TABLE Orders (
        OrderID INT PRIMARY KEY IDENTITY(1,1),
        OrderOriginalID NVARCHAR(50), -- ID gốc từ Olist
        CustomerID INT,
        OrderDate DATETIME,
        OrderStatus NVARCHAR(50),
        TotalAmount FLOAT,
        FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
    );

    -- 6. Bảng OrderItems
    CREATE TABLE OrderItems (
        OrderItemID INT PRIMARY KEY IDENTITY(1,1),
        OrderID INT,
        ProductID INT,
        Quantity INT DEFAULT 1,
        SellingPrice FLOAT, -- Giá bán thực tế lúc mua
        FreightValue FLOAT, -- Phí ship
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

    