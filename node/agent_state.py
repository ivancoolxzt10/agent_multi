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
    tool_finished: bool  # 是否所有工具调用都已完成
    called_tools:list
    tool_call_count: dict
    conversation_finished: bool