# main.py
import os
import uuid
import asyncio
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langchain_core.messages import HumanMessage, message_to_dict, messages_from_dict

from state import AgentState
from agents import NODES

# Kết nối Redis
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

# --- LOAD CONFIG TỪ .ENV ---
def _str_to_bool(value: str) -> bool:
    return value.lower() in ('true', '1', 'yes', 'on')

ENABLE_SEARCH = _str_to_bool(os.getenv("ENABLE_SEARCH_AGENT", "true"))
ENABLE_MATH = _str_to_bool(os.getenv("ENABLE_MATH_AGENT", "true"))
ENABLE_PETROL = _str_to_bool(os.getenv("ENABLE_PETROL_AGENT", "true"))

# Build Graph
workflow = StateGraph(AgentState)

# Luôn add router và responder
workflow.add_node("router", NODES["router"])
workflow.add_node("responder", NODES["responder"])

# Chỉ add agent nếu enabled
if ENABLE_SEARCH:
    workflow.add_node("search_agent", NODES["search_agent"])
if ENABLE_MATH:
    workflow.add_node("math_agent", NODES["math_agent"])
if ENABLE_PETROL:
    workflow.add_node("petrol_agent", NODES["petrol_agent"])

workflow.set_entry_point("router")

# --- LOGIC QUAN TRỌNG: ROUTING ---
def route_logic(state):
    step = state["next_step"]
    
    if isinstance(step, list):
        destinations = []
        for s in step:
            if s == "SEARCH" and ENABLE_SEARCH: 
                destinations.append("search_agent")
            elif s == "MATH" and ENABLE_MATH: 
                destinations.append("math_agent")
            elif s == "PETROL" and ENABLE_PETROL: 
                destinations.append("petrol_agent")
        return destinations if destinations else "responder"
    
    if step == "FINISH":
        return "responder"
    
    return "responder"

conditional_edges = ["responder"]
if ENABLE_SEARCH:
    conditional_edges.append("search_agent")
if ENABLE_MATH:
    conditional_edges.append("math_agent")
if ENABLE_PETROL:
    conditional_edges.append("petrol_agent")

workflow.add_conditional_edges("router", route_logic, conditional_edges)

if ENABLE_SEARCH:
    workflow.add_edge("search_agent", "router")
if ENABLE_MATH:
    workflow.add_edge("math_agent", "router")
if ENABLE_PETROL:
    workflow.add_edge("petrol_agent", "router")
workflow.add_edge("responder", END)


async def run_repl():
    """Interactive REPL giữ nguyên thread_id để test checkpoint Redis."""
    # Async checkpointer (RediSearch required)
    checkpointer = AsyncRedisSaver(redis_url)
    await checkpointer.setup()
    app = workflow.compile(checkpointer=checkpointer)

    thread_id = os.getenv("THREAD_ID") or str(uuid.uuid4())
    print(f"--- REPL (thread_id={thread_id}) ---")
    print(f"🔍 Search: {'✅' if ENABLE_SEARCH else '❌'} | 🧮 Math: {'✅' if ENABLE_MATH else '❌'} | ⛽ Petrol: {'✅' if ENABLE_PETROL else '❌'}")
    print("Nhập câu hỏi, Enter để thoát.")

    while True:
        try:
            query = input("User: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query:
            break

        config = {"configurable": {"thread_id": thread_id}}
        safe_query = query.encode("utf-8", "replace").decode("utf-8")
        inputs = {"messages": [message_to_dict(HumanMessage(content=safe_query))]}

        async for event in app.astream(inputs, config=config):
            print(f"🔄 Đang chạy Node: {list(event.keys())}")

        final = await app.aget_state(config)
        if final.values:
            msgs = messages_from_dict(final.values["messages"])
            print("🤖:", msgs[-1].content)
        print()


# --- CHẠY REPL ---
if __name__ == "__main__":
    asyncio.run(run_repl())
