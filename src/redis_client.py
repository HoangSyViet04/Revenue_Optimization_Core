import redis
import os
from datetime import datetime
from dotenv import load_dotenv
# 2. Gọi hàm này để nó load nội dung từ file .env vào bộ nhớ
load_dotenv()

# Cấu hình Redis (Có thể lấy từ biến môi trường hoặc mặc định localhost)
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
REDIS_DB = int(os.getenv("REDIS_DB"))

try:
    # Tạo kết nối
    # decode_responses=True để khi get về nó là String, không phải Bytes
    r = redis.Redis(
        host=REDIS_HOST, 
        port=REDIS_PORT, 
        db=REDIS_DB, 
        decode_responses=True
    )
    
    # Ping thử phát xem sống chết thế nào
    r.ping()
    print(f"Đã kết nối Redis tại {REDIS_HOST}:{REDIS_PORT}")

except redis.ConnectionError:
    print("CẢNH BÁO: Không thể kết nối Redis! Hệ thống sẽ chạy chậm hơn vì không có Cache.")
    r = None

def get_redis_client():
    """Hàm này trả về đối tượng kết nối Redis để các file khác dùng"""
    return r

def log_activity(action: str, details: str):
    """Ghi log hoạt động vào Redis List (Giữ lại 50 log gần nhất)"""
    if r:
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {action}: {details}"
        
        try:
            # LPUSH: Đẩy vào đầu danh sách
            r.lpush("system_logs", log_entry)
            # LTRIM: Chỉ giữ lại 50 dòng mới nhất, xóa cái cũ đi cho nhẹ
            r.ltrim("system_logs", 0, 49)
        except Exception as e:
            print(f"Lỗi ghi log: {e}")

def get_system_logs():
    """Lấy danh sách log từ Redis"""
    if r:
        return r.lrange("system_logs", 0, -1)
    return ["Redis is offline. No logs available."]
