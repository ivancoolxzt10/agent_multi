import operator
import json
import os
# graph.py
from typing import TypedDict, Annotated, Sequence, Literal

from langchain_core.messages import BaseMessage
from .session_db import SessionDB
import time


# 1. 精细化共享状态
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    user_info: str
    assigned_agent: Literal["presales", "aftersales", "receptionist"]
    tool_calls: list
    sessions_finished: bool  # 是否所有工具调用都已完成
    called_tools: dict   # 修正为 dict 类型
    tool_call_count: dict
    conversation_finished: bool
    can_reply_to_user: bool  # 当前结果是否可直接回复客户
    user_id: str
    queried_set: list  # 新增字段，已检索过的 query 集合

    @staticmethod
    def save_state(session_id: str, state: dict, path: str = './sessions/'):
        db = SessionDB()
        # 保存元数据
        db.save_meta(session_id, state)
        # 保存消息
        messages = state.get('all_messages', [])
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
        for m in messages:
            role = 'human'
            content = ''
            tool_call_id = None
            # 判断消息类型
            if isinstance(m, HumanMessage):
                role = 'human'
                content = m.content
            elif isinstance(m, AIMessage):
                role = 'ai'
                content = m.content
            elif isinstance(m, ToolMessage):
                role = 'tool'
                content = m.content
                tool_call_id = getattr(m, 'tool_call_id', None)
            elif hasattr(m, 'dict'):
                d = m.dict()
                role = d.get('role', 'human')
                content = str(d.get('content', ''))
                if role == 'tool':
                    tool_call_id = d.get('tool_call_id', None)
            elif isinstance(m, dict):
                role = m.get('role', 'human')
                content = str(m.get('content', ''))
                if role == 'tool':
                    tool_call_id = m.get('tool_call_id', None)
            elif isinstance(m, str):
                role = 'human'
                content = m
            elif hasattr(m, 'content'):
                role = getattr(m, 'role', 'human')
                content = str(m.content)
            else:
                role = 'human'
                content = str(m)
            db.save_message(session_id, role, content, int(time.time()), tool_call_id)

    @staticmethod
    def load_state(session_id: str, path: str = './sessions/') -> dict:
        db = SessionDB()
        meta = db.get_meta(session_id)
        raw_messages = db.get_messages(session_id, max_length=10)
        structured_messages = []
        from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
        for m in raw_messages:
            if isinstance(m, dict):
                role = m.get('role', 'human')
                content = m.get('content', '')
                if role == 'human':
                    structured_messages.append(HumanMessage(content=content))
                elif role == 'ai':
                    structured_messages.append(AIMessage(content=content))
                elif role == 'tool':
                    # ToolMessage 可能有 tool_call_id
                    tool_call_id = m.get('tool_call_id', None)
                    if tool_call_id:
                        structured_messages.append(ToolMessage(content=content, tool_call_id=tool_call_id))
                    else:
                        structured_messages.append(ToolMessage(content=content, tool_call_id=""))
                else:
                    structured_messages.append(HumanMessage(content=content))
            elif isinstance(m, str):
                structured_messages.append(HumanMessage(content=m))
            else:
                # 兼容已是 BaseMessage 的情况
                structured_messages.append(m)
        meta['messages'] = structured_messages
        return meta

    @staticmethod
    def trim_context(messages: Sequence[BaseMessage], max_length: int = 10) -> Sequence[BaseMessage]:
        # 只保留最近 max_length 条消息
        return messages[-max_length:] if len(messages) > max_length else messages
