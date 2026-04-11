import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

import pandas as pd
from mlxtend.frequent_patterns import fpgrowth, association_rules
from src.models.recsys_engineering import load_transaction_data, transform_data
import joblib

# Đường dẫn lưu model (thực ra là lưu bảng luật)
MODEL_DIR = os.path.join(os.path.dirname(__file__), '../../model_registry/recsys/')
os.makedirs(MODEL_DIR, exist_ok=True)

class RecommendationEngine:
    def __init__(self):
        self.rules = None

    def train(self, min_support=0.02, min_confidence=0.2):
        """
        Huấn luyện hệ thống gợi ý.
        - min_support: Tần suất xuất hiện tối thiểu của combo (2% đơn hàng).
        - min_confidence: Độ tin cậy tối thiểu (20%).
        """
        print("BẮT ĐẦU TÌM KIẾM LUẬT KẾT HỢP (ASSOCIATION RULES)...")
        
        # 1. Chuẩn bị dữ liệu
        raw_df = load_transaction_data()
        basket = transform_data(raw_df)
        
        # 2. Tìm Frequent Itemsets (Các bộ sản phẩm hay đi cùng nhau)
        # Dùng fpgrowth vì nó nhanh hơn Apriori với dữ liệu lớn
        print(f"-> Đang chạy FPGrowth (min_support={min_support})...")
        frequent_itemsets = fpgrowth(basket, min_support=min_support, use_colnames=True)
        print(f"-> Tìm thấy {len(frequent_itemsets)} bộ sản phẩm phổ biến.")

        # 3. Tạo luật kết hợp (Association Rules)
        print(f"-> Đang sinh luật kết hợp (min_confidence={min_confidence})...")
        self.rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
        
        # Sắp xếp theo độ mạnh của luật (Lift)
        # Lift > 1: Có mối quan hệ tích cực (Mua A thúc đẩy mua B)
        self.rules = self.rules.sort_values('lift', ascending=False)
        
        print(f"Đã tìm thấy {len(self.rules)} luật kết hợp!")
        
        # 4. Lưu kết quả
        rules_path = os.path.join(MODEL_DIR, 'association_rules.pkl')
        joblib.dump(self.rules, rules_path)
        print(f"Đã lưu bộ luật tại: {rules_path}")

        return self.rules

    def recommend(self, items_in_cart, top_k=3):
        """
        Gợi ý sản phẩm dựa trên giỏ hàng hiện tại.
        items_in_cart: List tên các category đang có trong giỏ (VD: ['bed_bath_table'])
        """
        if self.rules is None:
            print("Chưa có model. Hãy chạy train() trước.")
            return []
        
        # Tìm các luật mà 'antecedents' (Vế trái) nằm trong giỏ hàng
        # frozenset là định dạng của mlxtend
        
        # Logic: Lọc các luật mà vế trái (antecedents) là tập con của giỏ hàng
        cart_set = set(items_in_cart)
        
        # Lọc luật: Vế trái phải nằm trong giỏ hàng của khách
        # Ví dụ: Khách mua {A, B}. Luật {A} -> {C} (Thỏa mãn). Luật {A, D} -> {E} (Không thỏa mãn vì thiếu D).
        matching_rules = self.rules[self.rules['antecedents'].apply(lambda x: x.issubset(cart_set))]
        
        if matching_rules.empty:
            return []
        
        # Lấy vế phải (consequents) - tức là sản phẩm được gợi ý
        recommendations = []
        for _, row in matching_rules.head(top_k).iterrows():
            item = list(row['consequents'])[0]
            recommendations.append({
                'Product': item,
                'Confidence': round(row['confidence'], 2), # Độ chắc chắn
                'Reason': f"Customers who bought {list(row['antecedents'])} also bought {item}"
            })
            
        return recommendations

if __name__ == "__main__":
    recsys = RecommendationEngine()
    
    # 1. Train model
    recsys.train()
    
    # 2. Test thử gợi ý
    test_cart = ['WHITE HANGING HEART T-LIGHT HOLDER']  # Sản phẩm phổ biến trong UK Retail
    print(f"\nGiỏ hàng hiện tại: {test_cart}")
    print("Gợi ý:")
    recs = recsys.recommend(test_cart)
    for r in recs:
        print(f"- {r['Product']} (Độ tin cậy: {r['Confidence']}) | {r['Reason']}")