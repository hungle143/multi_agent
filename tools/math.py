import math
import asyncio


async def math_tool(expression: str):
    print(f"   🧮 [TOOL] Đang tính toán: {expression}")
    try:
        def _calc():
            # 1. Định nghĩa môi trường an toàn (chỉ cho phép dùng thư viện math)
            safe_env = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}

            # 2. Xử lý string đầu vào (clean up)
            expression_clean = expression.replace("=", "").strip()

            # 3. Tính toán trong môi trường safe_env
            result = eval(expression_clean, {"__builtins__": None}, safe_env)
            return str(result)

        return await asyncio.to_thread(_calc)
    except Exception as e:
        return f"Lỗi tính toán: {str(e)}. (Hãy đảm bảo dùng đúng cú pháp Python math, ví dụ: sqrt(25))"
