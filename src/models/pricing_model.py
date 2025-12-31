import sys
import os
# Fix đường dẫn
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import matplotlib.pyplot as plt
import mlflow
import mlflow.lightgbm

from src.models.feature_engineering import load_sales_data, generate_features

# Đường dẫn lưu model
MODEL_DIR = os.path.join(os.path.dirname(__file__), '../../model_registry/pricing/')
os.makedirs(MODEL_DIR, exist_ok=True)

class DemandForecastingModel:
    def __init__(self):
        self.model = None
        self.features = [
            'AvgPrice', 'CompetitorPrice', 'Price_Ratio', 
            'Elasticity', 'Days_Since_Last_Sale', 'Days_To_Stockout',
            'Rolling_Sales_7d', 'Lag_Sales_1d',
            'Month', 'Quarter', 'IsWeekend', 'CurrentStock'
        ]
        self.target = 'QuantitySold'
        
        # Cấu hình MLflow
        # Nó sẽ tạo thư mục 'mlruns' để lưu lịch sử
        mlflow.set_tracking_uri("file:./mlruns")
        mlflow.set_experiment("RevenueCore_Demand_Forecast")

    def prepare_data(self, min_sales_threshold=50):
        # ... (Giữ nguyên logic cũ) ...
        raw_df = load_sales_data()
        df = generate_features(raw_df)
        
        product_stats = df.groupby('ProductID')['QuantitySold'].sum()
        top_products = product_stats[product_stats > min_sales_threshold].index.tolist()
        df_filtered = df[df['ProductID'].isin(top_products)].copy()
        
        print(f"\n📊 DATA STATS:")
        print(f"- Kích thước tập train: {df_filtered.shape}")
        return df_filtered

    def train(self):
        print("\n🚀 BẮT ĐẦU TRAIN MODEL (CÓ MLFLOW TRACKING)...")
        
        # Bắt đầu 1 lượt chạy mới (Run)
        with mlflow.start_run():
            # 1. Chuẩn bị dữ liệu
            df = self.prepare_data()
            X = df[self.features]
            y = df[self.target]
            
            # Log danh sách features đang dùng
            mlflow.log_param("features_list", ", ".join(self.features))
            mlflow.log_param("data_shape", df.shape)

            # 2. Chia Train/Test
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
            
            # 3. Cấu hình Hyperparams
            params = {
                'objective': 'regression',
                'metric': 'rmse',
                'boosting_type': 'gbdt',
                'learning_rate': 0.05,
                'num_leaves': 31,
                'feature_fraction': 0.9
            }
            # Log tham số cấu hình
            mlflow.log_params(params)
            
            train_data = lgb.Dataset(X_train, label=y_train)
            test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
            
            # 4. Training
            self.model = lgb.train(
                params,
                train_data,
                num_boost_round=1000,
                valid_sets=[test_data],
                callbacks=[lgb.early_stopping(stopping_rounds=50)]
            )
            
            # 5. Đánh giá
            y_pred = self.model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            print(f"\n🏆 KẾT QUẢ: MAE={mae:.4f} | RMSE={rmse:.4f}")
            
            # Log kết quả metrics vào MLflow
            mlflow.log_metric("mae", mae)
            mlflow.log_metric("rmse", rmse)
            
            # Log (Lưu) Model vào MLflow luôn
            mlflow.lightgbm.log_model(self.model, "model")

            # 6. Lưu Model ra file local (để dùng cho bước Optimize)
            model_path = os.path.join(MODEL_DIR, 'lgbm_demand_v1.pkl')
            joblib.dump(self.model, model_path)
            print(f"✅ Đã lưu model tại: {model_path}")
            
        return self.model

if __name__ == "__main__":
    bot = DemandForecastingModel()
    bot.train()