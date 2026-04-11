from pydantic import BaseModel
from typing import List, Optional

# Input: Tối ưu giá cho 1 sản phẩm
class PricingRequest(BaseModel):
    product_id: int

# Output: Kết quả tối ưu giá
class PricingResponse(BaseModel):
    product_id: int
    current_price: float
    optimal_price: float
    predicted_revenue: float
    revenue_uplift: str

# Input: Gợi ý sản phẩm từ giỏ hàng
class RecommendationRequest(BaseModel):
    cart_items: List[str]

# Output: Danh sách gợi ý
class RecommendationResponse(BaseModel):
    input_cart: List[str]
    recommendations: List[dict]
    message: str