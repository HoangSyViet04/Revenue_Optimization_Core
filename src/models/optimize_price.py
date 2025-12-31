import sys
import os
# Fix đường dẫn
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pandas as pd
import numpy as np
import joblib
from src.models.feature_engineering import load_sales_data, generate_features

# Load Model đã train ở bước trước
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../../model_registry/pricing/lgbm_demand_v1.pkl')

class PriceOptimizer:
    def __init__(self):
        print("Đang tải Model AI...")
        try:
            self.model = joblib.load(MODEL_PATH)
            print("Đã tải Model thành công!")
        except FileNotFoundError:
            print("Chưa thấy file model. Hãy chạy pricing_model.py trước!")
            sys.exit()

        # Danh sách features phải KHỚP 100% lúc train
        self.features = [
            'AvgPrice', 'CompetitorPrice', 'Price_Ratio', 
            'Elasticity', 'Days_Since_Last_Sale', 'Days_To_Stockout',
            'Rolling_Sales_7d', 'Lag_Sales_1d',
            'Month', 'Quarter', 'IsWeekend', 'CurrentStock'
        ]

    def optimize_single_product(self, product_id, current_price, features_df):
        """
        Chạy mô phỏng để tìm giá tối ưu cho 1 sản phẩm.
        """
        # 1. Lấy thông tin features mới nhất của SP đó
        # (Lấy dòng dữ liệu ngày gần nhất)
        product_data = features_df[features_df['ProductID'] == product_id].iloc[[-1]].copy()
        
        if product_data.empty:
            return None

        print(f"\n🔍 Đang tối ưu giá cho SP: {product_id} (Giá hiện tại: {current_price}$)")

        # 2. Tạo dải giá giả định (Simulation Range)
        # Thử từ -20% đến +20% giá hiện tại, bước nhảy 5%
        price_multipliers = [0.8, 0.85, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2]
        results = []

        base_competitor_price = product_data['CompetitorPrice'].values[0]

        for mult in price_multipliers:
            # Tạo kịch bản giá mới
            sim_price = current_price * mult
            
            # Cập nhật các feature liên quan đến giá
            sim_data = product_data.copy()
            sim_data['AvgPrice'] = sim_price
            sim_data['Price_Ratio'] = sim_price / (base_competitor_price + 0.01)
            
            # 3. Model dự báo nhu cầu (AI Prediction)
            predicted_qty = self.model.predict(sim_data[self.features])[0]
            
            # Không thể bán số lượng âm
            predicted_qty = max(0, predicted_qty)
            
            # 4. Tính doanh thu dự kiến
            predicted_revenue = sim_price * predicted_qty
            
            results.append({
                'Scenario': f"{int((mult-1)*100)}%", # -20%, +10%...
                'Price': round(sim_price, 2),
                'Predicted_Sales': round(predicted_qty, 2),
                'Revenue': round(predicted_revenue, 2)
            })

        # 5. Chuyển thành bảng và tìm giá ngon nhất
        df_results = pd.DataFrame(results)
        best_scenario = df_results.loc[df_results['Revenue'].idxmax()].copy()
        
        # Tính Revenue Uplift (So với kịch bản hiện tại 0%)
        current_rev_row = df_results[df_results['Scenario'] == "0%"]
        if not current_rev_row.empty:
            current_revenue = current_rev_row['Revenue'].values[0]
            if current_revenue > 0:
                uplift = ((best_scenario['Revenue'] - current_revenue) / current_revenue) * 100
                best_scenario['Revenue_Uplift'] = f"{uplift:+.1f}%"
            else:
                best_scenario['Revenue_Uplift'] = "0.0%"
        else:
            best_scenario['Revenue_Uplift'] = "N/A"

        print("--- BẢNG MÔ PHỎNG GIÁ ---")
        print(df_results.to_string(index=False))
        print(f"GIÁ TỐI ƯU: {best_scenario['Price']} (Doanh thu dự kiến: {best_scenario['Revenue']})")
        print("-" * 30)
        
        return best_scenario

    def run_demo(self):
        # Load lại dữ liệu mới nhất để lấy feature
        raw = load_sales_data()
        df = generate_features(raw)
        
        # Chọn 1 sản phẩm bán chạy nhất để Demo
        top_product = df.groupby('ProductID')['QuantitySold'].sum().idxmax()
        
        # Lấy giá hiện tại (giá lần bán cuối cùng)
        current_price = df[df['ProductID'] == top_product]['AvgPrice'].iloc[-1]
        
        self.optimize_single_product(top_product, current_price, df)

if __name__ == "__main__":
    optimizer = PriceOptimizer()
    optimizer.run_demo()