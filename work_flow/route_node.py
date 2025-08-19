from langchain_core.messages import ToolMessage

from work_flow.agent_state import AgentState
from agents.after_sales_v_agent import aftersales_chain
from agents.pre_sales_agent import presales_chain
from work_flow.data_dto import ToolCallRequest
from work_flow.utils import debug_handler


def specialist_node(state: AgentState):
    agent_role = state["assigned_agent"]
    print(f"--- 节点: {agent_role.capitalize()}专家 ---")

    chain = presales_chain if agent_role == "presales" else aftersales_chain

    # 调用原始链，得到一个 AIMessage
    ai_response_message = chain.invoke({"messages": state["messages"]},config={"callbacks": [debug_handler]})

    # **核心健aprobst性处理：手动解析 AIMessage 的 tool_calls**
    tool_calls_to_execute = []
    speak_content = ""

    # 检查 AIMessage 是否包含有效的 tool_calls
    parsed = ai_response_message.get("parsed")
    raw = ai_response_message.get("raw")

    # 新增：如果会话已结束，则不再继续调用工具
    can_reply_to_user = state.get("can_reply_to_user", False)
    if parsed and parsed.tool_calls and len(parsed.tool_calls) > 0 and not can_reply_to_user:
        print(f"专家请求工具调用: {parsed.tool_calls}")
        for call in parsed.tool_calls:
            # 自动补充 user_id 参数
            params = dict(call.parameters) if call.parameters else {}
            if 'user_id'  in params:
                # user_info 可能是字符串，需要转为 int
                try:
                    params['user_id'] = int(state.get('user_id', 0))
                except Exception:
                    params['user_id'] = state.get('user_id', 0)
            tool_calls_to_execute.append(
                ToolCallRequest(tool_name=call.tool_name, parameters=params)
            )
    else:
        speak_content = getattr(parsed, "speak", "")

    if raw and getattr(raw, "content", None):
        speak_content = raw.content
    tool_messages = []
    print(f"专家回复内容: {speak_content}")
    if speak_content:
        tool_messages.append(ToolMessage(content=speak_content, tool_call_id="speak_to_user"))
    return {
        "tool_calls": tool_calls_to_execute,
        "messages":  tool_messages ,
    }
