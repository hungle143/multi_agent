from agents.router import orchestrator_node
from agents.search_agent import search_worker
from agents.math_agent import math_worker
from agents.petrol_agent import petrol_worker
from agents.responder import responder_node

# Registry tên node -> hàm thực thi
NODES = {
    "router": orchestrator_node,
    "search_agent": search_worker,
    "math_agent": math_worker,
    "petrol_agent": petrol_worker,
    "responder": responder_node,
}

__all__ = [
    "orchestrator_node",
    "search_worker",
    "math_worker",
    "responder_node",
    "NODES",
]
