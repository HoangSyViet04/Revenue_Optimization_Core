import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# Import cả 2 model
from src.models.optimize_price import PriceOptimizer
from src.models.feature_engineering import load_sales_data, generate_features
from src.models.recsys_model import RecommendationEngine

# Import Redis Client
from src.redis_client import get_redis_client, log_activity, get_system_logs

app = FastAPI(title="RevenueCore: Pricing & RecSys AI", version="2.0")

# Khởi tạo Redis Client
redis_client = get_redis_client()

# --- GLOBAL VARIABLES (CACHE RAM) ---
price_optimizer = None
latest_features = None
recsys_engine = None

# --- REQUEST MODELS ---
class ProductRequest(BaseModel):
    product_id: int

class RecommendationRequest(BaseModel):
    cart_items: List[str]  # Ví dụ: ["bed_bath_table", "watches_gifts"]

# --- STARTUP EVENT ---
@app.on_event("startup")
def load_resources():
    global price_optimizer, latest_features, recsys_engine
    print("Đang khởi động hệ thống RevenueCore AI...")
    
    # 1. Load Pricing Model
    print("... Loading Pricing Model & Data")
    price_optimizer = PriceOptimizer()
    raw_data = load_sales_data()
    latest_features = generate_features(raw_data)
    
    # 2. Load Recommendation Model
    # Chạy lại train với tham số nhỏ để load luật vào RAM
    print("... Loading Recommendation Engine")
    recsys_engine = RecommendationEngine()
    # Dùng đúng tham số ông vừa chạy thành công
    recsys_engine.train(min_support=0.00005, min_confidence=0.005)
    
    print("SERVER ĐÃ SẴN SÀNG! (Pricing + RecSys Ready)")

# --- ENDPOINTS ---

@app.get("/")
def home():
    return {"message": "RevenueCore AI is running!"}

# API MỚI: Lấy danh sách Logs
@app.get("/logs")
def get_logs_endpoint():
    logs = get_system_logs()
    return {"logs": logs}

# API 1: Tối ưu giá (CÓ REDIS CACHE)
@app.post("/optimize")
def optimize_price_endpoint(request: ProductRequest):
    global price_optimizer, latest_features
    
    pid = request.product_id
    
    # 1. Check Redis Cache
    cache_key = f"price_opt:{pid}"
    if redis_client:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            print(f"CACHE: Lấy giá tối ưu từ Redis cho {pid}")
            log_activity("CACHE HIT", f"Price Optimization for Product {pid}")
            return json.loads(cached_data)

    # 2. Miss Cache -> Tính toán
    print(f"MISS CACHE: Đang tính toán giá cho {pid}...")
    if pid not in latest_features['ProductID'].values:
        raise HTTPException(status_code=404, detail="Product ID not found")
    
    current_price = latest_features[latest_features['ProductID'] == pid]['AvgPrice'].iloc[-1]
    result = price_optimizer.optimize_single_product(pid, current_price, latest_features)
    
    if result is None:
        raise HTTPException(status_code=500, detail="Optimization failed")
    
    response_data = {
        "product_id": pid,
        "current_price": current_price,
        "optimal_price": result['Price'],
        "predicted_revenue": result['Revenue'],
        "revenue_uplift": result['Revenue_Uplift']
    }
    
    log_activity("AI COMPUTE", f"Optimized Price for Product {pid}")

    # 3. Save to Redis (TTL: 1 hour)
    if redis_client:
        redis_client.setex(cache_key, 3600, json.dumps(response_data))
    
    return response_data

# API 2: Gợi ý sản phẩm 
@app.post("/recommend")
def recommend_endpoint(request: RecommendationRequest):
    global recsys_engine
    
    if not request.cart_items:
         raise HTTPException(status_code=400, detail="Cart is empty")

    # Tạo key cache dựa trên danh sách sản phẩm (đã sort để tránh trùng lặp thứ tự)
    sorted_cart = sorted(request.cart_items)
    cache_key = f"rec:{json.dumps(sorted_cart)}"
    
    # 1. Check Redis Cache
    if redis_client:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            print(f"CACHE: Lấy gợi ý từ Redis cho {sorted_cart}")
            log_activity("CACHE HIT", f"Recommendations for cart {request.cart_items}")
            return json.loads(cached_data)

    # 2. Miss Cache -> Tính toán
    print(f"🛒 MISS CACHE: Đang tìm gợi ý cho {request.cart_items}")
    recommendations = recsys_engine.recommend(request.cart_items)
    
    response_data = {
        "input_cart": request.cart_items,
        "recommendations": recommendations,
        "message": "Buy these together!" if recommendations else "No strong patterns found."
    }
    
    log_activity("AI COMPUTE", f"Generated recommendations for {len(request.cart_items)} items")

    # 3. Save to Redis (TTL: 24 hours - Luật gợi ý ít thay đổi hơn giá)
    if redis_client:
        redis_client.setex(cache_key, 86400, json.dumps(response_data))
    
    return response_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)