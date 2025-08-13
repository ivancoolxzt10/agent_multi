import operator
# graph.py
from typing import TypedDict, Annotated, Sequence, Literal

from langchain_core.messages import BaseMessage


# 1. 精细化共享状态
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_info: str
    assigned_agent: Literal["presales", "aftersales", "receptionist"]
    tool_calls: list
    conversation_finished: bool