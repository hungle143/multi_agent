from langchain_core.messages import SystemMessage, messages_from_dict, message_to_dict, AIMessage

from state import AgentState
from prompts import RESPONDER_SYSTEM_PROMPT
from agents.shared import llm


async def responder_node(state: AgentState):
    messages = messages_from_dict(state["messages"])
    
    # Kiểm tra xem có disabled agent message không
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content.startswith("[DISABLED]"):
            # LLM sẽ xử lý message này dựa trên prompt
            break
    
    response = await llm.ainvoke([SystemMessage(content=RESPONDER_SYSTEM_PROMPT)] + messages)
    return {"messages": [message_to_dict(response)]}
