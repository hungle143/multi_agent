import os
import httpx


async def petrol_tool(fuel_type: str | None, region: str = "vung_1") -> str:
    """
    Gọi API giá xăng nội bộ. Không fallback sang nguồn khác.
    Trả về chuỗi kết quả hoặc thông báo lỗi.
    """
    base_url = os.getenv("PETROL_API_BASE_URL", "http://127.0.0.1:8000")
    base = base_url.rstrip("/")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if fuel_type:
                url = f"{base}/prices/search"
                params = {"type": fuel_type, "region": region}
                resp = await client.get(url, params=params)
            else:
                url = f"{base}/prices/all"
                resp = await client.get(url)
            # Ưu tiên surface lỗi từ API
            if resp.status_code >= 400:
                detail = None
                try:
                    detail = resp.json().get("detail")
                except Exception:
                    pass
                return f"Lỗi API xăng ({resp.status_code}): {detail or resp.text}"

            data = resp.json()
            if fuel_type:
                price = data.get("price")
                unit = data.get("unit", "VND/lít")
                fuel = data.get("fuel_type", fuel_type)
                reg = data.get("region", region)
                return f"Giá {fuel} tại {reg}: {price} {unit}"
            else:
                # Trả về tóm tắt nhanh cho cả bảng giá
                prices = data.get("data") or {}
                parts = []
                for reg, fuels in prices.items():
                    summary = "; ".join([f"{k}={v}" for k, v in fuels.items()])
                    parts.append(f"{reg}: {summary}")
                if parts:
                    return "Bảng giá xăng/dầu: " + " | ".join(parts)
                return "Không có dữ liệu giá."
    except httpx.RequestError as e:
        return f"Lỗi kết nối API xăng: {str(e)}"
