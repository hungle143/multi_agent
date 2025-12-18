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

# Build Graph
workflow = StateGraph(AgentState)
for name, node in NODES.items():
    workflow.add_node(name, node)

workflow.set_entry_point("router")

# --- LOGIC QUAN TRỌNG: ROUTING ---
def route_logic(state):
    # Lấy giá trị next_step từ output của Router Node
    step = state["next_step"]
    
    # Nếu Router trả về List (Chạy song song)
    if isinstance(step, list):
        # Map từ Keyword sang Tên Node
        destinations = []
        for s in step:
            if s == "SEARCH": destinations.append("search_agent")
            elif s == "MATH": destinations.append("math_agent")
            elif s == "PETROL": destinations.append("petrol_agent")
        return destinations # Trả về list các node cần đến
    
    # Nếu trả về string đơn (FINISH)
    if step == "FINISH":
        return "responder"
    
    return "responder" # Fallback

workflow.add_conditional_edges(
    "router",
    route_logic,
    # Map các khả năng có thể xảy ra
    ["search_agent", "math_agent", "petrol_agent", "responder"] 
)

workflow.add_edge("search_agent", "router")
workflow.add_edge("math_agent", "router")
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
