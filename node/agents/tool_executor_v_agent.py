# -*- coding: utf-8 -*-

from langchain_core.messages import ToolMessage
from node.agent_state import AgentState
from node.utils import all_tools_map


# --- ToolExecutorAgent ---
def tool_executor_node(state: AgentState):
    print("--- 节点: 工具执行员 ---")
    tool_calls = state["tool_calls"]
    tool_messages = []
    for call in tool_calls:
        tool_name = call.tool_name
        args = call.parameters
        print(f"正在执行工具: {tool_name} with args {args}")
        if tool_name not in all_tools_map:
            result = f"错误: 工具 '{tool_name}' 不存在。"
        else:
            try:
                tool_func = all_tools_map[tool_name]
                result = tool_func.invoke(args)
            except Exception as e:
                result = f"工具执行出错: {e}"

        tool_messages.append(ToolMessage(content=str(result), name=tool_name, tool_call_id=f"call_{tool_name}"))

    print(f"工具执行结果: {tool_messages}")
    return {
        "messages": tool_messages,
        "tool_calls": []  # 清空工具调用请求
    }