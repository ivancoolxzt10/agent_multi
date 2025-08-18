from typing import Literal

from pydantic import BaseModel, Field


# 2. Pydantic 模型用于结构化输出
class TriageResult(BaseModel):
    """用于封装客服请求分诊结果的结构。"""
    agent_role: Literal["presales", "aftersales"] = Field(
        description="根据用户意图分析后，最终指派的专家角色。"
    )
    user_info: str = Field(
        description="从用户问题中提取出的关键实体信息，如订单号、用户ID或商品ID。如果没有，则返回'N/A'。"
    )
    user_id: str = Field(
        default="0",
        description="默认不填充,使用 0 作为占位符。",
    )

class ReplyResult(BaseModel):
    """用于封装客服回复结果的结构。"""
    summarize_context: str = Field(
        description="只保留用户的意图和关键信息",
        strict=False
    )
    reply_context: str = Field(
        description="改善整理之后,回复用户的信息。"
    )
    can_reply_to_user: bool = Field(
        default=False,
        description="当前结果是否可直接回复客户"
    )

class ToolCallRequest(BaseModel):
    """一个具体的工具调用请求。"""
    tool_name: str = Field(description="需要调用的工具名称。")
    parameters: dict = Field(description="调用该工具所需的参数字典。")


class AgentDecision(BaseModel):
    """专家 Agent 的决策，包含回复和工具调用。"""
    speak: str = Field(description="需要对用户说的回复内容。")
    tool_calls: list[ToolCallRequest] = Field(description="一个包含零个或多个工具调用请求的列表。")
    can_reply_to_user: bool = Field(
        default=False,
        description="当前结果是否可直接回复客户"
    )