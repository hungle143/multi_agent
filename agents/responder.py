from langchain_core.messages import SystemMessage, messages_from_dict, message_to_dict

from state import AgentState
from prompts import RESPONDER_SYSTEM_PROMPT
from agents.shared import llm


async def responder_node(state: AgentState):
    messages = messages_from_dict(state["messages"])
    response = await llm.ainvoke([SystemMessage(content=RESPONDER_SYSTEM_PROMPT)] + messages)
    return {"messages": [message_to_dict(response)]}
