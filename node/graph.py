# graph.py
from langgraph.graph import StateGraph

from node.agent_state import AgentState
from node.agents.quality_control_agent import quality_control_node
from node.agents.receptionist_agent import receptionist_node
from node.agents.tool_executor_v_agent import tool_executor_node
from node.route_node import specialist_node


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
        # 获取工具调用次数的字典，默认为空
        tool_call_count = state["tool_call_count"] if "tool_call_count" in state else {}
        if state.get("tool_finished"):
            # 如果对话已经结束，直接进入质量控制
            return "quality_control"
        # 检查是否有工具调用
        if state.get("tool_calls"):
            for tool_call in state["tool_calls"]:
                tool_name = tool_call.tool_name
                parameters = tool_call.parameters

                # 构造唯一标识（工具名+参数）
                tool_key = f"{tool_name}"

                # 检查调用次数是否超过限制
                if tool_call_count.get(tool_key, 0) >= 3:  # 假设最大调用次数为 3
                    print(f"工具 {tool_name} 已达到最大调用次数，跳过调用。")
                    continue

                # 增加调用次数
                tool_call_count[tool_key] = tool_call_count.get(tool_key, 0) + 1

                # 记录调用过的工具并返回工具执行节点
                state.setdefault("called_tools", {})[tool_key] = True
                return "tool_executor"

        # 如果没有工具调用，直接进入质量控制
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