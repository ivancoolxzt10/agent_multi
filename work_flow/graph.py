# graph.py
from langgraph.graph import StateGraph

from work_flow.agent_state import AgentState
from work_flow.agents.quality_control_agent import quality_control_node
from work_flow.agents.receptionist_agent import receptionist_node
from work_flow.agents.tool_executor_v_agent import tool_executor_node
from work_flow.route_node import specialist_node


# 4. 构建图
def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("receptionist", receptionist_node)
    workflow.add_node("presales", specialist_node)
    workflow.add_node("aftersales", specialist_node)
    workflow.add_node("tool_executor", tool_executor_node)
    workflow.add_node("quality_control", quality_control_node)

    workflow.set_entry_point("receptionist")

    # 定义路由逻辑
    def route_after_reception(state: AgentState):
        return state["assigned_agent"]

    def route_after_specialist(state: AgentState):
        tool_call_count = state.get("tool_call_count", {})
        if not isinstance(tool_call_count, dict):
            tool_call_count = {}
        # 获取工具调用次数的字典，默认为空
        queried_set = set(state.get("queried_set", []))
        # 新增：记录已检索过的 query，防止重复调用
        if state.get("sessions_finished"):
            # 如果对话已经结束，直接进入质量控制
            return "quality_control"
        # 检查是否有工具调用
        if state.get("tool_calls"):
            new_tool_calls = []
            for tool_call in state["tool_calls"]:
                tool_name = tool_call.tool_name
                parameters = tool_call.parameters
                # 打印当前工具调用的角色信息
                sender_role = getattr(tool_call, "sender_role", None)
                receiver_role = getattr(tool_call, "receiver_role", None)
                print(f"[工具调用日志] tool_name: {tool_name}, sender_role: {sender_role}, receiver_role: {receiver_role}, parameters: {parameters}")
                # 构造唯一标识（工具名+参数）
                tool_key = f"{tool_name}:{str(parameters)}"
                # 针对 knowledge_base_retriever 做 query 去重
                if tool_name == "knowledge_base_retriever":
                    query = parameters.get("query")
                    if query in queried_set:
                        print(f"query '{query}' 已检索过，跳过重复调用。")
                        continue
                    queried_set.add(query)
                # 检查调用次数是否超过限制
                if tool_call_count.get(tool_key, 0) >= 3:  # 假设最大调用次数为 3
                    print(f"工具 {tool_name} 已达到最大调用次数，跳过调用。")
                    continue
                # 增加调用次数
                tool_call_count[tool_key] = tool_call_count.get(tool_key, 0) + 1
                new_tool_calls.append(tool_call)
            # 更新 state（全局统一处理，不分当前/历史）
            state["tool_call_count"] = tool_call_count
            state["queried_set"] = list(queried_set)
            state["tool_calls"] = new_tool_calls
            if new_tool_calls:
                return "tool_executor"
        # 没有工具调用或全部被去重/限制，进入质量控制
        return "quality_control"

    def route_after_tools(state: AgentState):
        # 工具执行完，返回给之前分配的专家继续对话
        return state["assigned_agent"]

    # 添加边
    workflow.add_conditional_edges("receptionist", route_after_reception)
    workflow.add_conditional_edges("presales", route_after_specialist)
    workflow.add_conditional_edges("aftersales", route_after_specialist)
    workflow.add_conditional_edges("tool_executor", route_after_tools)
    workflow.add_edge("quality_control", "__end__")

    app = workflow.compile()
    return app


graph_app = build_graph()