from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import random

app = FastAPI(title="Petrol Price API", version="1.0")

# 1. Giả lập Database giá xăng (Đơn vị: VNĐ/lít)
# Cập nhật ngày: 16/12/2025 (Giả định)
MOCK_DATABASE = {
    "vung_1": {
        "ron95-iii": 22790,
        "e5_ron92": 21680,
        "diesel": 20190,
        "dau_hoa": 20880
    },
    "vung_2": {
        "ron95-iii": 23240,
        "e5_ron92": 22110,
        "diesel": 20590,
        "dau_hoa": 21290
    }
}

# 2. API Endpoint: Lấy tất cả giá
@app.get("/prices/all")
async def get_all_prices():
    """Trả về toàn bộ bảng giá xăng dầu"""
    return {
        "status": "success",
        "currency": "VND",
        "data": MOCK_DATABASE
    }

# 3. API Endpoint: Tra cứu cụ thể (Agent sẽ dùng cái này)
@app.get("/prices/search")
async def search_price(type: str, region: str = "vung_1"):
    """
    Tra cứu giá theo loại xăng và vùng.
    - type: ron95-iii, e5_ron92, diesel
    - region: vung_1 (mặc định), vung_2
    """
    
    # Chuẩn hóa đầu vào (lowercase)
    reg_key = region.lower()
    type_key = type.lower()

    # Logic xử lý lỗi (Để Agent bắt lỗi này)
    if reg_key not in MOCK_DATABASE:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy vùng '{region}'. Chỉ hỗ trợ: vung_1, vung_2")

    prices = MOCK_DATABASE[reg_key]

    if type_key not in prices:
        # Nếu Agent hỏi loại xăng không tồn tại
        valid_types = list(prices.keys())
        raise HTTPException(
            status_code=404, 
            detail=f"Loại xăng '{type}' không tồn tại. Các loại hỗ trợ: {valid_types}"
        )
    
    # Trả về kết quả đẹp
    return {
        "fuel_type": type_key,
        "region": reg_key,
        "price": prices[type_key],
        "unit": "VND/lite"
    }

# 4. API Endpoint: Giả lập lỗi Server (Để test độ bền của Agent)
@app.get("/system/status")
async def check_health():
    # Giả vờ server chập chờn (xác suất 30% chết)
    if random.random() < 0.3:
        raise HTTPException(status_code=500, detail="Database connection failed")
    return {"status": "ok"}