from work_flow.agents.receptionist_agent import receptionist_agent
from work_flow.agents.complaint_agent import complaint_agent
from work_flow.agents.quality_control_agent import quality_control_agent
from work_flow.route_node import specialist_node
from work_flow.agents.tool_executor_v_agent import tool_executor_node

NODES = {
    "receptionist": receptionist_agent.agent_node,
    "presales": specialist_node,
    "aftersales": specialist_node,
    "tool_executor": tool_executor_node,
    "quality_control": quality_control_agent.quality_control_node,
    "complaint": complaint_agent.agent_node,
}
