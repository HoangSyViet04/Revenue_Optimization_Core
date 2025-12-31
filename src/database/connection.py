from sqlalchemy import create_engine
from src.config import Config

def get_db_engine():
    """Tạo và trả về Engine kết nối SQL Server"""
    try:
        conn_str = Config.get_connection_string()
        engine = create_engine(conn_str)
        # Test kết nối nhẹ cái
        with engine.connect() as conn:
            pass
        return engine
    except Exception as e:
        print(f"Lỗi kết nối SQL Server: {e}")
        raise e