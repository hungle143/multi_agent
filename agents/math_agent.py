from langchain_core.messages import AIMessage, messages_from_dict, message_to_dict

from state import AgentState
from prompts import MATH_EXTRACT_PROMPT
from tools import math_tool
from agents.shared import llm


async def math_worker(state: AgentState):
    messages = messages_from_dict(state["messages"])

    # 1. Gom context toàn bộ lịch sử để Math Agent "nhìn" thấy kết quả Search
    full_context = "\n".join([f"{msg.type}: {msg.content}" for msg in messages])

    # 2. Inject context vào Prompt chuẩn
    formatted_prompt = MATH_EXTRACT_PROMPT.format(context_text=full_context)

    # 3. Gọi LLM
    expression = (await llm.ainvoke(formatted_prompt)).content.strip()
    print(f"   🧮 [Math Logic] Phép tính tìm được: {expression}")

    # 4. Tính toán
    result = await math_tool(expression)
    safe = str(result).encode("utf-8", "replace").decode("utf-8")
    return {"messages": [message_to_dict(AIMessage(content=f"[KẾT QUẢ TÍNH TOÁN]: {safe}"))]}
