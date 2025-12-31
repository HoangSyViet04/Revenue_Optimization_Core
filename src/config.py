import os
from dotenv import load_dotenv
import urllib
from pathlib import Path

# Load biến môi trường từ file .env
load_dotenv()

# Định nghĩa đường dẫn gốc của Project để tránh lỗi "File not found"
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')

class Config:
    SERVER = os.getenv('DB_SERVER')
    DATABASE = os.getenv('DB_NAME')
    USERNAME = os.getenv('DB_USER')
    PASSWORD = os.getenv('DB_PASSWORD')
    DRIVER = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')

    @staticmethod
    def get_connection_string():
        # Xử lý ký tự đặc biệt trong password
        params = urllib.parse.quote_plus(
            f'DRIVER={{{Config.DRIVER}}};'
            f'SERVER={{{Config.SERVER}}};'
            f'DATABASE={{{Config.DATABASE}}};'
            f'UID={{{Config.USERNAME}}};'
            f'PWD={{{Config.PASSWORD}}};'
            'TrustServerCertificate=yes;'
        )
        return f'mssql+pyodbc:///?odbc_connect={params}'