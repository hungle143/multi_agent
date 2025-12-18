import os
import httpx


async def search_tool(query: str):
    print(f"   🔎 [TOOL] Đang tìm trên Tavily: '{query}'...")
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Lỗi Search: Thiếu API Key Tavily."

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": 3,
        "include_images": False,
        "include_answers": False,
    }
    headers = {"Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post("https://api.tavily.com/search", json=payload, headers=headers)
            if resp.status_code >= 400:
                return f"Lỗi Search {resp.status_code}: {resp.text}"

            data = resp.json()
            results = data.get("results") or []
            if results:
                top = results[0]
                content = top.get("content", "")
                url = top.get("url", "")
                return f"Nội dung từ {url}: {content}"
            return "Không tìm thấy kết quả nào."
    except httpx.RequestError as e:
        return f"Lỗi Search (kết nối): {str(e)}"
    except Exception as e:
        return f"Lỗi Search: {str(e)}"
