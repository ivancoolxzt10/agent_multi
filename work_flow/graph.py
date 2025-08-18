# graph.py
from langgraph.graph import StateGraph

from work_flow.agent_state import AgentState
from work_flow.workflow_nodes import NODES
from work_flow.workflow_routes import route_after_reception, route_after_specialist, route_after_tools, route_after_complaint


# 构建工作流主流程，支持动态入口节点
def build_graph(entry_agent="receptionist"):
    workflow = StateGraph(AgentState)
    # 注册节点
    for node_name, node_func in NODES.items():
        workflow.add_node(node_name, node_func)
    workflow.set_entry_point(entry_agent)
    # 路由绑定
    workflow.add_conditional_edges("receptionist", route_after_reception)
    workflow.add_conditional_edges("presales", route_after_specialist)
    workflow.add_conditional_edges("aftersales", route_after_specialist)
    workflow.add_conditional_edges("tool_executor", route_after_tools)
    workflow.add_conditional_edges("complaint", route_after_complaint)
    workflow.add_edge("quality_control", "__end__")

    app = workflow.compile()
    return app


# 默认入口节点由主流程动态指定，移除静态 entry_agent 和 graph_app 实例化
# 使用 build_graph(entry_agent) 动态构建
