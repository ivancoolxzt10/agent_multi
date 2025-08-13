import os
from dotenv import load_dotenv
from typing import Any, Dict, List, Union

from langchain_core.prompts import ChatPromptTemplate
from typing import Literal
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult
# 导入回调处理器基类
from langchain_core.callbacks.base import BaseCallbackHandler

class DebugCallbackHandler(BaseCallbackHandler):
    """一个自定义的回调处理器，用于打印LLM的详细交互过程。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm_input_messages = ""
        self.llm_output_raw = ""

    def on_llm_start(
            self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> Any:
        """当LLM接收到提示词并准备开始时触发。"""
        # 在 `with_structured_output` 模式下，prompts 是一个字符串列表
        # 但我们更关心发送给模型的实际消息对象，这在 kwargs['invocation_params']['messages'] 中
        # 为了通用性，我们先记录 prompts
        print("\n" + "---" * 10)
        print("🚀 [EVENT] on_llm_start: LLM即将被调用...")
        print("\n" + "---" * 10)
        print(f"prompts:",prompts)

        # 打印传递给LLM的完整参数，这对于调试至关重要
        # 它包含了模型名称、工具、消息等所有信息
        invocation_params = kwargs.get('invocation_params', {})
        print(f"🔧 [LLM INPUT] 调用参数: {invocation_params}")

        # 特别是 messages 部分
        messages_to_llm = invocation_params.get('messages', [[]])[0]
        self.llm_input_messages = "\n".join([f"  - {type(msg).__name__}: {msg.content}" for msg in messages_to_llm])
        print(f"💬 [LLM INPUT] 发送给LLM的消息:")
        print(self.llm_input_messages)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        """当LLM完成生成并返回结果时触发。"""
        print("\n✅ [EVENT] on_llm_end: LLM调用完成。")
        self.llm_output_raw = response.generations[0][0].message
        print(f"📦 [LLM OUTPUT] LLM原始返回 (AIMessage对象):")
        print(f"  - Content: '{self.llm_output_raw.content}'")
        print(f"  - Tool Calls: {self.llm_output_raw.tool_calls}")
        print("---" * 10 + "\n")
