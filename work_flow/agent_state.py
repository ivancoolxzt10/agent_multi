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
    assigned_agent: Literal["presales", "aftersales", "receptionist", "complaint", "quality_control"]
    last_business_agent: str  # 新增：记录最后一个实际业务处理 agent
    tool_calls: list
    sessions_finished: bool  # 是否所有工具调用都已完成
    called_tools: dict   # 修正为 dict 类型
    tool_call_count: dict
    conversation_finished: bool
    can_reply_to_user: bool  # 当前结果是否可直接回复客户
    user_id: str
    queried_set: list  # 新增字段，已检索过的 query 集合
    context: dict  # 新增：上下文信息（如当前节点、异常、优先级等）
    history: list  # 新增：流程轨迹、工具调用历史、异常等

    def get(self, key, default=None):
        return self[key] if key in self else default

    def set(self, key, value):
        self[key] = value

    def add_history(self, event):
        if "history" not in self:
            self["history"] = []
        self["history"].append(event)

    @staticmethod
    def get_last_business_agent(state_or_meta):
        # 优先从 history 查找最近的 agent 切换事件
        history = state_or_meta.get('history', [])
        for event in reversed(history):
            # 假定切换事件格式为 {'event': 'switch_agent', 'agent': 'xxx'}
            if isinstance(event, dict) and event.get('event') == 'switch_agent':
                agent = event.get('agent')
                if agent and agent != 'quality_control':
                    return agent
        # 从 messages 查找最近的非质检 agent
        messages = state_or_meta.get('messages', [])
        from langchain_core.messages import AIMessage, ToolMessage
        for m in reversed(messages):
            # AIMessage/ToolMessage 需有 agent 字段或 role 字段
            agent = None
            if hasattr(m, 'agent'):
                agent = getattr(m, 'agent')
            elif hasattr(m, 'role'):
                agent = getattr(m, 'role')
            elif isinstance(m, dict):
                agent = m.get('agent') or m.get('role')
            if agent and agent != 'quality_control':
                return agent
        # 如果都没有，默认 receptionist
        return 'receptionist'

    @staticmethod
    def save_state(session_id: str, state: dict, path: str = './sessions/'):
        db = SessionDB()
        meta = dict(state)
        # 保存元数据，确保 assigned_agent 被写入
        if 'messages' in meta:
            del meta['messages']
        if 'all_messages' in meta:
            del meta['all_messages']
        # 补全 assigned_agent 字段
        if 'assigned_agent' not in meta or not meta['assigned_agent']:
            meta['assigned_agent'] = state.get('assigned_agent', 'receptionist')
        # 补全 last_business_agent 字段，特殊处理质检 agent
        if 'last_business_agent' not in meta or not meta['last_business_agent']:
            if meta['assigned_agent'] == 'quality_control':
                meta['last_business_agent'] = AgentState.get_last_business_agent(state)
            else:
                meta['last_business_agent'] = state.get('last_business_agent', meta['assigned_agent'])
        db.save_meta(session_id, meta)
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
                structured_messages.append(m)
        # 字段补全，保证 assigned_agent、tool_calls 等关键字段存在
        if meta is None:
            meta = {}
        meta['messages'] = structured_messages
        if 'assigned_agent' not in meta or not meta['assigned_agent']:
            meta['assigned_agent'] = "receptionist"
        # 补全 last_business_agent 字段
        if 'last_business_agent' not in meta or not meta['last_business_agent']:
            if meta['assigned_agent'] == 'quality_control':
                meta['last_business_agent'] = AgentState.get_last_business_agent(meta)
            else:
                meta['last_business_agent'] = meta['assigned_agent']
        if 'tool_calls' not in meta:
            meta['tool_calls'] = []
        if 'called_tools' not in meta:
            meta['called_tools'] = {}
        if 'tool_call_count' not in meta:
            meta['tool_call_count'] = {}
        if 'history' not in meta:
            meta['history'] = []
        if 'queried_set' not in meta:
            meta['queried_set'] = []
        if 'sessions_finished' not in meta:
            meta['sessions_finished'] = False
        if 'conversation_finished' not in meta:
            meta['conversation_finished'] = False
        if 'user_info' not in meta:
            meta['user_info'] = ""
        if 'can_reply_to_user' not in meta:
            meta['can_reply_to_user'] = False
        if 'user_id' not in meta:
            meta['user_id'] = ""
        return meta

    @staticmethod
    def trim_context(messages: Sequence[BaseMessage], max_length: int = 10) -> Sequence[BaseMessage]:
        # 只保留最近 max_length 条消息
        return messages[-max_length:] if len(messages) > max_length else messages
