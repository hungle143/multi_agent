import operator
from typing import TypedDict, Annotated, Sequence

# Định nghĩa cấu trúc dữ liệu di chuyển giữa các nodes
class AgentState(TypedDict):
    # messages: Lưu lịch sử chat (dùng operator.add để nối thêm chứ không ghi đè)
    # Lưu dạng dict (message_to_dict) để dễ serialize checkpoint Redis
    messages: Annotated[Sequence[dict], operator.add]
    # next_step: Cờ hiệu để Router chỉ đường (SEARCH, MATH, FINISH)
    next_step: str
