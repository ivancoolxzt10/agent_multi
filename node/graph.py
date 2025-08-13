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
        if state.get("tool_calls") and len(state["tool_calls"]) > 0:
            return "tool_executor"
        # 简化逻辑：如果没有工具调用，就认为对话可以结束了。
        # 真实场景需要更复杂的判断，比如用户是否说了“谢谢”或“再见”。
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