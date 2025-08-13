
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from callbacks.callback_handler import DebugCallbackHandler
from llm import llm
from node.data_dto import AgentDecision
from node.tools.aftersales_tools import aftersales_tool_list
from node.tools.presales_tools import presales_tool_list

# 创建回调处理器的实例
debug_handler = DebugCallbackHandler()

# --- 专家 Agent (通用逻辑) ---
def create_specialist_chain(system_prompt: str, tools: list):
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
    ])

    return prompt | llm.with_structured_output(AgentDecision, include_raw=True)


# 合并所有工具，供 ToolExecutorAgent 使用
all_tools_map = {t.name: t for t in presales_tool_list + aftersales_tool_list}

