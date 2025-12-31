from pydantic import BaseModel

# Input: Khi gửi request lên, bắt buộc phải có đủ các trường này
class PricingRequest(BaseModel):
    current_price : float
    competitor_price : float
    stock_level : int
    is_weekend : int
    category_code : int

# Output: Server trả về kết quả này
class PricingResponse(BaseModel):
    suggested_price :float
    expected_revenue : float
    message : str