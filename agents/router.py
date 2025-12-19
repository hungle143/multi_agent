import re
import os
from dotenv import load_dotenv
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
    messages_from_dict,
    message_to_dict,
)

from state import AgentState
from prompts import ROUTER_SYSTEM_PROMPT
from agents.shared import llm

load_dotenv()

# Load config
def _str_to_bool(value: str) -> bool:
    return value.lower() in ('true', '1', 'yes', 'on')

ENABLE_SEARCH = _str_to_bool(os.getenv("ENABLE_SEARCH_AGENT", "true"))
ENABLE_MATH = _str_to_bool(os.getenv("ENABLE_MATH_AGENT", "true"))
ENABLE_PETROL = _str_to_bool(os.getenv("ENABLE_PETROL_AGENT", "true"))


async def orchestrator_node(state: AgentState):
    raw_messages = messages_from_dict(state["messages"])

    def sanitize(msg: AIMessage | HumanMessage):
        safe_content = msg.content.encode("utf-8", "replace").decode("utf-8")
        return msg.copy(update={"content": safe_content})

    messages = [sanitize(m) for m in raw_messages]
    # Lấy human cuối và text lower để nhận diện nhanh ý định
    last_human_text = ""
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_human_text = msg.content.lower()
            break

    def has_marker_after_last_human(marker: str) -> bool:
        # Tìm human cuối cùng
        last_human = -1
        for idx in range(len(messages) - 1, -1, -1):
            if isinstance(messages[idx], HumanMessage):
                last_human = idx
                break
        if last_human == -1:
            return False
        for msg in messages[last_human + 1 :]:
            if isinstance(msg, AIMessage) and marker in msg.content:
                return True
        return False

    search_done = has_marker_after_last_human("[KẾT QUẢ SEARCH]")
    math_done = has_marker_after_last_human("[KẾT QUẢ TÍNH TOÁN]")
    petrol_done = has_marker_after_last_human("[KẾT QUẢ XĂNG]")

    response = await llm.ainvoke([SystemMessage(content=ROUTER_SYSTEM_PROMPT)] + messages)
    decision_string = response.content.strip().upper()

    # Xử lý chuỗi trả về thành List (SEARCH, MATH, PETROL)
    decisions = [x.strip() for x in decision_string.split(",")]

    # Heuristic: nếu câu hỏi có nhắc giá xăng/dầu thì bắt buộc thêm PETROL
    fuel_terms = ["xăng", "xang", "ron95", "ron 95", "ron92", "ron 92", "e5", "dầu", "dau", "diesel", "dầu hoả", "dau hoa"]
    fuel_detect = any(term in last_human_text for term in fuel_terms)

    # Heuristic: nhận diện nhu cầu search khác (thời tiết, tin tức) để giữ SEARCH khi cần song song
    search_terms = ["thời tiết", "thoi tiet", "dự báo", "du bao", "tin tức", "tin tuc", "news", "tìm", "tim", "tra cứu", "tracuu"]
    wants_search = any(term in last_human_text for term in search_terms)

    # Heuristic: nhận diện phép tính đơn giản để ưu tiên MATH
    math_detect = bool(re.search(r"\d+\s*([+*/x:-]|\^)\s*\d+", last_human_text)) or any(
        phrase in last_human_text for phrase in ["bằng mấy", "bang may", "kết quả", "ket qua"]
    )

    # Heuristic: nhận diện chào/tạm biệt/cảm ơn để cho FINISH
    smalltalk_terms = ["kết thúc", "ket thuc", "tạm biệt", "tam biet", "bye", "cảm ơn", "cam on", "hello", "hi", "chào", "chao"]
    smalltalk_detect = any(term in last_human_text for term in smalltalk_terms)

    if fuel_detect and "PETROL" not in decisions:
        decisions.append("PETROL")
    # Nếu chỉ hỏi giá xăng/dầu (không có ý định search thứ khác), bỏ SEARCH khỏi quyết định để tránh web search
    if fuel_detect and not wants_search:
        decisions = [d for d in decisions if d != "SEARCH"]

    # Fallback: nếu chưa quyết định
    if (
        (not search_done)
        and (not math_done)
        and (not petrol_done)
        and (not decisions or decisions == [""])
    ):
        if math_detect:
            decisions = ["MATH"]
        elif fuel_detect:
            decisions = ["PETROL"]
        elif wants_search:
            decisions = ["SEARCH"]
        elif smalltalk_detect:
            decisions = ["FINISH"]
        else:
            decisions = ["FINISH"]

    # Lọc keyword hợp lệ - kiểm tra enabled agents
    final_actions = []
    disabled_agents_used = []
    
    if "SEARCH" in decisions and not search_done:
        if ENABLE_SEARCH:
            final_actions.append("SEARCH")
        else:
            disabled_agents_used.append("SEARCH")
    
    if "MATH" in decisions and not math_done:
        if ENABLE_MATH:
            final_actions.append("MATH")
        else:
            disabled_agents_used.append("MATH")
    
    if "PETROL" in decisions and not petrol_done:
        if ENABLE_PETROL:
            final_actions.append("PETROL")
        else:
            disabled_agents_used.append("PETROL")

    # Xử lý disabled agents
    if disabled_agents_used and not final_actions:
        # TẤT CẢ agents yêu cầu đều disabled
        agent_names = {"SEARCH": "Search", "MATH": "Math", "PETROL": "Petrol"}
        disabled_msg = f"[DISABLED]: {', '.join([agent_names[a] for a in disabled_agents_used])}"
        return {
            "next_step": "FINISH",
            "messages": [message_to_dict(AIMessage(content=disabled_msg))]
        }
    
    if disabled_agents_used and final_actions:
        # CÓ agents enabled nhưng CÓ agents bị disable -> notify
        agent_names = {"SEARCH": "Search", "MATH": "Math", "PETROL": "Petrol"}
        disabled_msg = f"[PARTIAL]: {', '.join([agent_names[a] for a in disabled_agents_used])}"
        return {
            "next_step": final_actions,
            "messages": [message_to_dict(AIMessage(content=disabled_msg))]
        }

    # Default là FINISH
    if not final_actions or "FINISH" in decisions:
        return {"next_step": "FINISH"}

    return {"next_step": final_actions}
