import re
from langchain_core.messages import AIMessage, HumanMessage, messages_from_dict, message_to_dict

from state import AgentState
from tools import petrol_tool

# Marker to detect đã xử lý giá xăng trong lượt user hiện tại
PETROL_MARKER = "[KẾT QUẢ XĂNG]"


def _extract_params(messages) -> tuple[str | None, str]:
    """Rút loại xăng và vùng từ lịch sử (ưu tiên human cuối)."""
    # Lấy human cuối cùng
    user_text = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_text = msg.content.lower()
            break

    region = "vung_1"
    if re.search(r"v[ùu]ng\\s*2", user_text) or "khu 2" in user_text:
        region = "vung_2"

    fuel_type = None
    if "95" in user_text or "ron95" in user_text:
        fuel_type = "ron95-iii"
    elif "92" in user_text or "e5" in user_text:
        fuel_type = "e5_ron92"
    elif "diesel" in user_text or "dầu diesel" in user_text:
        fuel_type = "diesel"
    elif "dầu hỏa" in user_text or "dau hoa" in user_text:
        fuel_type = "dau_hoa"

    return fuel_type, region


async def petrol_worker(state: AgentState):
    messages = messages_from_dict(state["messages"])
    fuel_type, region = _extract_params(messages)
    result = await petrol_tool(fuel_type, region)
    safe = str(result).encode("utf-8", "replace").decode("utf-8")
    return {"messages": [message_to_dict(AIMessage(content=f"{PETROL_MARKER}: {safe}"))]}
