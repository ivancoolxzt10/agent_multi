# -*- coding: utf-8 -*-
import json

from langchain_core.messages import ToolMessage
from work_flow.agent_state import AgentState
from work_flow.utils import all_tools_map


# --- ToolExecutorAgent ---
def tool_executor_node(state: AgentState):
    print("--- 节点: 工具执行员 ---")
    tool_calls = state["tool_calls"]
    tool_messages = []
    for call in tool_calls:
        tool_name = call.tool_name
        args = call.parameters
        print(f"正在执行工具: {tool_name} with args {args}")
        tool_message_content = ""  # 初始化，确保所有分支有值
        if tool_name not in all_tools_map:
            result = f"错误: 工具 '{tool_name}' 不存在。"
            tool_message_content = json.dumps({"error": result}, ensure_ascii=False)
        else:
            try:
                tool_func = all_tools_map[tool_name]
                result = tool_func.invoke(args)
                can_reply_to_user = False
                if isinstance(result, dict):
                    # 兼容不同拼写
                    if "can_reply_to_user" in result:
                        can_reply_to_user = result["can_reply_to_user"]
                    elif "session_finished" in result:
                        can_reply_to_user = result["session_finished"]
                    elif "sessions_finished" in result:
                        can_reply_to_user = result["sessions_finished"]
                    if can_reply_to_user:
                        state["can_reply_to_user"] = True
                        print("结果可直接回复客户。")
                    else:
                        state["can_reply_to_user"] = False
                        print("结果暂不可直接回复客户，需继续处理。")
                    # 仅日志打印知识库内容，不拼接到 ToolMessage
                    if "knowledge_base_result" in result:
                        explain = "\n".join([item["content"] for item in result["knowledge_base_result"]])
                        print(f"知识库检索结果日志: {explain}")
                        # ToolMessage 的 content 用结构化 json，增加 message_type 标识
                        tool_message_content = json.dumps({
                            "message_type": "knowledge_base",
                            "result": result,
                            "can_reply_to_user": can_reply_to_user
                        }, ensure_ascii=False)
                    else:
                        # 其他工具结果
                        tool_message_content = json.dumps({
                            "message_type": "tool",
                            "result": result
                        }, ensure_ascii=False)
                else:
                    tool_message_content = str(result)
            except Exception as e:
                tool_message_content = json.dumps({"error": str(e)}, ensure_ascii=False)
        tool_messages.append(ToolMessage(content=tool_message_content, name=tool_name, tool_call_id=f"call_{tool_name}"))

    print(f"工具执行结果: {tool_messages}")
    return {
        "messages": tool_messages,
        "can_reply_to_user": state.get("can_reply_to_user", False),
        "tool_calls": []  # 清空工具调用请求
    }