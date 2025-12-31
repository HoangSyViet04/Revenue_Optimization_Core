# 🚀 RevenueCore: AI-Powered Revenue Optimization Engine

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-1.22%2B-FF4B4B)
![Redis](https://img.shields.io/badge/Redis-Caching-red)
![License](https://img.shields.io/badge/License-MIT-green)

> **RevenueCore** là hệ thống thông minh toàn diện (end-to-end) được thiết kế để tối đa hóa doanh thu thương mại điện tử thông qua **Định giá động (Dynamic Pricing)** (sử dụng LightGBM) và **Cá nhân hóa gợi ý (Personalized Recommendations)** (sử dụng luật kết hợp FP-Growth). Hệ thống sở hữu API hiệu năng cao tích hợp Redis caching cùng Dashboard quản trị trực quan.

---

## 💼 Tổng quan dự án (Business Value)

Trong thương mại điện tử, hai bài toán lớn nhất ảnh hưởng trực tiếp đến doanh thu là:
1. **Mất khách do giá không linh hoạt:** Giá cố định không phản ánh được cung cầu thực tế và biến động thị trường.
2. **Giá trị đơn hàng thấp (Low AOV):** Khách hàng không tìm thấy sản phẩm mua kèm phù hợp, bỏ lỡ cơ hội Cross-sell.

**RevenueCore giải quyết vấn đề này bằng cách:**
- 🔹 **Tự động đề xuất mức giá tối ưu** dựa trên dữ liệu lịch sử, giá đối thủ và độ co giãn của cầu.
- 🔹 **Gợi ý sản phẩm mua kèm (Cross-sell)** với độ chính xác cao bằng thuật toán **FP-Growth**.
- 🔹 **Tối ưu hiệu năng hệ thống** bằng Redis Caching, đảm bảo phản hồi **< 10ms** ngay cả khi chịu tải cao.

---

## 🌟 Tính năng nổi bật
### 1. 💰 Bộ máy Định giá Động (Dynamic Pricing Engine)

- **Tối ưu hóa thời gian thực:** Phân tích lịch sử bán hàng, giá đối thủ và độ co giãn của cầu để đề xuất mức giá tối ưu nhất.
- **Dự báo tăng trưởng doanh thu:** Tự động tính toán mức doanh thu tiềm năng so với giá hiện tại.
- **Mô phỏng nhu cầu (Demand Simulation):** Trực quan hóa tác động của thay đổi giá đối với sản lượng bán hàng dự kiến bằng mô phỏng Parabolic.

### 2. 🛒 Hệ thống Gợi ý Thông minh (Cross-Selling)

- **Phân tích giỏ hàng (Market Basket Analysis):** Sử dụng thuật toán FP-Growth để khám phá các mối liên kết mạnh mẽ giữa sản phẩm.
- **Nhận biết ngữ cảnh:** Gợi ý sản phẩm dựa trên thành phần giỏ hàng hiện tại của người dùng.
- **Xếp hạng độ tin cậy:** Sắp xếp các gợi ý theo độ tin cậy thống kê (Confidence Score) để đảm bảo tính liên quan cao nhất.

### 3. ⚡ Kiến trúc Hiệu năng cao

- **Redis Caching:** Triển khai chiến lược caching cho cả API Định giá và Gợi ý, giảm độ trễ cho các truy vấn thường xuyên xuống dưới 10ms.
- **Audit Logging:** Theo dõi thời gian thực các hoạt động hệ thống (Cache Hits/Misses, tính toán AI) và lưu trữ trong Redis.
- **Thiết kế mở rộng:** Kiến trúc tách biệt (Decoupled) với các module riêng biệt cho ETL, Modeling, API và Dashboard.

## 🏗 Kiến trúc hệ thống

Hệ thống được thiết kế theo mô hình Cache-Aside kết hợp với Clean Architecture để tối ưu hiệu suất và khả năng bảo trì.

```mermaid
graph TD
    User[User / Dashboard] -- 1. Request Price/Recs --> Main[FastAPI Backend]
    Main -- 2. Check Cache --> Redis[(Redis In-Memory)]
    
    Redis -- 3a. Cache Hit (Data Found) --> Main
    
    Redis -- 3b. Cache Miss (Not Found) --> Main
    Main -- 4. Run Algorithm --> AI_Engine[AI Core (LightGBM / FP-Growth)]
    AI_Engine -- 5. Return Result --> Main
    Main -- 6. Save to Cache (TTL) --> Redis
    Main -- 7. Show Data --> User
    
    style Redis fill:#ff4d4d,stroke:#333,stroke-width:2px,color:white
    style Main fill:#009688,stroke:#333,stroke-width:2px,color:white
    style AI_Engine fill:#4d79ff,stroke:#333,stroke-width:2px,color:white
```

## 🛠️ Công nghệ sử dụng (Tech Stack)

| Hạng mục | Công nghệ |
|----------|-----------|
| **Core** | Python 3.10+ |
| **Machine Learning** | LightGBM, Scikit-learn, MLxtend (FP-Growth), Pandas, NumPy |
| **Backend API** | FastAPI, Uvicorn, Pydantic |
| **Frontend** | Streamlit, Plotly (Biểu đồ tương tác) |
| **Database & Cache** | Redis (Caching & Logs), SQL Server |
| **MLOps** | MLflow (Quản lý thí nghiệm, model registry, tracking, deployment) |

## 📂 Cấu trúc dự án

Dự án tuân theo nguyên lý Clean Architecture để đảm bảo tính dễ bảo trì và mở rộng.
```bash
RevenueCore/
│
├── .env                       # Cấu hình môi trường (Redis Host, Secrets)
├── docker-compose.yml         # Điều phối Container
├── requirements.txt           # Các thư viện phụ thuộc
│
├── src/                       # CORE LOGIC (Lõi xử lý)
│   ├── redis_client.py        # Kết nối Redis & Wrapper ghi Log
│   ├── database/              # Xử lý kết nối Database
│   ├── etl/                   # Pipelines Trích xuất-Chuyển đổi-Nạp dữ liệu
│   └── models/                # Mô hình AI/ML
│       ├── optimize_price.py      # Logic định giá (LightGBM)
│       ├── pricing_model.py      
│       ├── recsys_model.py        # Logic gợi ý (FP-Growth)
│       ├── recsys_engineering.py       
│       └── feature_engineering.py # Tiền xử lý dữ liệu
│
├── api/                       # BACKEND (FastAPI)
│   ├── main.py                # Điểm khởi chạy API & Endpoints
│   └── schemas.py             # Mô hình dữ liệu Pydantic
│
├── dashboard/                 # FRONTEND (Streamlit)
│   └── app.py                 # Giao diện Admin Dashboard
│
├── data/                      # KHO DỮ LIỆU
│   └── raw/                   # Dữ liệu thô (Dataset Olist)
│   
│
└── model_registry/            # KHO MODEL
    ├── pricing/               # Model định giá đã huấn luyện (.pkl)
    └── recsys/                # Luật kết hợp đã lưu (.pkl)
```

## 🚀 Cài đặt & Hướng dẫn sử dụng

### Yêu cầu tiên quyết

- Python 3.10+
- Redis Server (Chạy local hoặc qua Docker)

### 1. Clone dự án

```bash
git clone https://github.com/HoangSyViet04/Revenue_Optimization_Core.git
cd RevenueCore
```

### 2. Thiết lập môi trường

Tạo môi trường ảo và cài đặt các thư viện phụ thuộc:

```bash
python -m venv venv
venv\Scripts\activate  
pip install -r requirements.txt
```

### 3. Cấu hình biến môi trường

Tạo file `.env` tại thư mục gốc:

```properties
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 4. Chạy hệ thống

**Bước 1: Khởi động Backend API**

```bash
uvicorn api.main:app --reload
```

API sẽ chạy tại: http://127.0.0.1:8000

**Bước 2: Khởi động Admin Dashboard**

```bash
streamlit run dashboard/app.py
```

Dashboard sẽ mở tại: http://localhost:8501

## 📊 Kịch bản sử dụng (Usage Scenarios)

### Kịch bản A: Quản lý giá (Pricing Manager)

1. Đăng nhập vào Dashboard.
2. Nhập Product ID (ví dụ: 9662).
3. Xem so sánh Giá hiện tại vs. Giá tối ưu AI.
4. Phân tích Biểu đồ doanh thu để thấy thay đổi giá ảnh hưởng thế nào đến nhu cầu.

### Kịch bản B: Quản trị viên hệ thống

1. Theo dõi Activity Logs (Nhật ký hoạt động) ở thanh bên.
2. Kiểm tra chỉ số Cache Hits để đảm bảo Redis đang tối ưu hóa hiệu suất.
3. Kiểm tra trạng thái sức khỏe hệ thống (Health Check).

## 🔮 Định hướng phát triển (Roadmap)

- [ ] Tích hợp framework A/B Testing cho các chiến lược giá.
- [ ] Nâng cấp Recommender Engine sang Deep Learning.
- [ ] Triển khai lên AWS/GCP sử dụng Kubernetes.
- [ ] Thêm xác thực người dùng & Phân quyền (RBAC).

## 👨‍💻 Tác giả

**[Hoang Sy Viet]**
Data Scientist / AI Engineer
