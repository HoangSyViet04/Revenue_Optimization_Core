import sys
import os
import json
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

# Import cả 2 model
from src.models.optimize_price import PriceOptimizer
from src.models.feature_engineering import load_sales_data, generate_features
from src.models.recsys_model import RecommendationEngine

# Import Redis Client
from src.redis_client import get_redis_client, log_activity, get_system_logs

app = FastAPI(title="RevenueCore: Pricing & RecSys AI", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo Redis Client
redis_client = get_redis_client()

# --- GLOBAL VARIABLES (CACHE RAM) ---
price_optimizer = None
latest_features = None
recsys_engine = None
product_info = None

# --- REQUEST MODELS ---
class ProductRequest(BaseModel):
    product_id: int

class RecommendationRequest(BaseModel):
    cart_items: List[str]  # Ví dụ: ["bed_bath_table", "watches_gifts"]

# --- STARTUP EVENT ---
@app.on_event("startup")
def load_resources():
    global price_optimizer, latest_features, recsys_engine, product_info
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
    # UK Retail dataset: support=2%, confidence=20% (dữ liệu phong phú hơn)
    recsys_engine.train(min_support=0.02, min_confidence=0.2)
    
    # 3. Load Product Info (for /products/top and /popular-items)
    print("... Loading Product Info from SQL")
    try:
        from src.database.connection import get_db_engine
        _engine = get_db_engine()
        product_info = pd.read_sql("SELECT ProductID, Description, BasePrice FROM Products", _engine)
        print(f"... Loaded {len(product_info)} products")
    except Exception as e:
        print(f"... Warning: Could not load product info: {e}")

    print("SERVER ĐÃ SẴN SÀNG! (Pricing + RecSys Ready)")

# --- ENDPOINTS ---

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/app")

@app.get("/health")
def health_check():
    return {"message": "RevenueCore AI is running!"}

@app.get("/app", response_class=HTMLResponse, include_in_schema=False)
def serve_dashboard():
    html_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        return f.read()

# Activity Logs
@app.get("/logs")
def get_logs_endpoint():
    logs = get_system_logs()
    return {"logs": logs}

# Top selling products (for dashboard dropdown)
@app.get("/products/top")
def get_top_products():
    global latest_features, product_info
    if latest_features is None or product_info is None:
        return {"products": []}
    top_pids = (
        latest_features.groupby('ProductID')['QuantitySold']
        .sum().sort_values(ascending=False).head(30).index.tolist()
    )
    result = []
    for pid in top_pids:
        row = product_info[product_info['ProductID'] == pid]
        if not row.empty:
            result.append({
                "id": int(pid),
                "description": str(row['Description'].iloc[0]),
                "base_price": round(float(row['BasePrice'].iloc[0]), 2)
            })
    return {"products": result}

# Popular item descriptions (for recommendation cart selector)
@app.get("/popular-items")
def get_popular_items():
    global latest_features, product_info
    if latest_features is None or product_info is None:
        return {"items": []}
    top_pids = (
        latest_features.groupby('ProductID')['QuantitySold']
        .sum().sort_values(ascending=False).head(80).index.tolist()
    )
    items = []
    seen = set()
    for pid in top_pids:
        row = product_info[product_info['ProductID'] == pid]
        if not row.empty:
            desc = str(row['Description'].iloc[0]).strip()
            if desc and desc not in seen:
                seen.add(desc)
                items.append(desc)
        if len(items) >= 40:
            break
    return {"items": items}

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
        "current_price": round(float(current_price), 2),
        "optimal_price": result['Price'],
        "predicted_revenue": result['Revenue'],
        "revenue_uplift": result['Revenue_Uplift'],
        "simulation": result.get('simulation', [])
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