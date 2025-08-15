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

    @staticmethod
    def save_state(session_id: str, state: dict, path: str = './sessions/'):
        db = SessionDB()
        # 保存元数据
        db.save_meta(session_id, state)
        # 保存消息
        messages = state.get('all_messages', [])
        for m in messages:
            # 兼容 dict、BaseMessage、str
            if hasattr(m, 'dict'):
                d = m.dict()
                role = d.get('role', 'human')
                content = str(d.get('content', ''))
            elif isinstance(m, dict):
                role = m.get('role', 'human')
                content = str(m.get('content', ''))
            elif isinstance(m, str):
                role = 'human'
                content = m
            elif hasattr(m, 'content'):
                role = getattr(m, 'role', 'human')
                content = str(m.content)
            else:
                role = 'human'
                content = str(m)
            db.save_message(session_id, role, content, int(time.time()))

    @staticmethod
    def load_state(session_id: str, path: str = './sessions/') -> dict:
        db = SessionDB()
        meta = db.get_meta(session_id)
        messages = db.get_messages(session_id, max_length=10)
        meta['messages'] = messages
        return meta

    @staticmethod
    def trim_context(messages: Sequence[BaseMessage], max_length: int = 10) -> Sequence[BaseMessage]:
        # 只保留最近 max_length 条消息
        return messages[-max_length:] if len(messages) > max_length else messages
