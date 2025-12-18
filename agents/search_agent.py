from langchain_core.messages import AIMessage, HumanMessage, messages_from_dict, message_to_dict

from state import AgentState
from tools import search_tool


async def search_worker(state: AgentState):
    # Lấy query cuối cùng từ người dùng
    msgs = messages_from_dict(state["messages"])
    last_msg = msgs[-1]
    query = last_msg.content
    for msg in reversed(msgs):
        if isinstance(msg, HumanMessage):
            query = msg.content
            break

    result = await search_tool(query)
    safe_result = result.encode("utf-8", "replace").decode("utf-8")
    return {"messages": [message_to_dict(AIMessage(content=f"[KẾT QUẢ SEARCH]: {safe_result}"))]}
