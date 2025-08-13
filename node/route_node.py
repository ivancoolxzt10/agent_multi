from langchain_core.messages import ToolMessage

from node.agent_state import AgentState
from node.agents.after_sales_v_agent import aftersales_chain
from node.agents.pre_sales_agent import presales_chain
from node.data_dto import ToolCallRequest
from node.utils import debug_handler


def specialist_node(state: AgentState):
    agent_role = state["assigned_agent"]
    print(f"--- 节点: {agent_role.capitalize()}专家 ---")

    chain = presales_chain if agent_role == "presales" else aftersales_chain

    # 调用原始链，得到一个 AIMessage
    ai_response_message = chain.invoke({"messages": state["messages"]},config={"callbacks": [debug_handler]})
    print("ai_response_message:", ai_response_message)

    # **核心健aprobst性处理：手动解析 AIMessage 的 tool_calls**
    tool_calls_to_execute = []
    speak_content = ""

    # 检查 AIMessage 是否包含有效的 tool_calls
    parsed = ai_response_message.get("parsed")
    raw = ai_response_message.get("raw")

    tool_calls_to_execute = []
    speak_content = ""

    if parsed and parsed.tool_calls and len(parsed.tool_calls) > 0:
        print(f"专家请求工具调用: {parsed.tool_calls}")
        for call in parsed.tool_calls:
            tool_calls_to_execute.append(
                ToolCallRequest(tool_name=call.tool_name, parameters=call.parameters)
            )
    else:
        speak_content = getattr(parsed, "speak", "")

    if raw and getattr(raw, "content", None):
        speak_content = raw.content

    print(f"专家回复内容: {speak_content}")
    print(f"待执行工具: {tool_calls_to_execute}")

    if speak_content:
        state["messages"].append(ToolMessage(content=speak_content, tool_call_id="speak_to_user"))

    return {
        "tool_calls": tool_calls_to_execute
    }
