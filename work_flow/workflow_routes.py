from work_flow.tool_call_policy import ToolCallPolicy
from work_flow.agent_state import AgentState

def route_after_reception(state: AgentState):
    return state.get("assigned_agent")


def route_after_specialist(state: AgentState):
    # 兼容 dict 类型的 state
    def add_history(event):
        if isinstance(state, dict):
            state.setdefault("history", []).append(event)
        else:
            state.add_history(event)
    policy = ToolCallPolicy(max_calls=3)
    tool_call_count = state.get("tool_call_count", {})
    queried_set = set(state.get("queried_set", []))
    if state.get("sessions_finished"):
        add_history({"event": "session_finished", "node": "specialist"})
        return "quality_control"
    new_tool_calls = []
    for tool_call in state.get("tool_calls", []):
        tool_name = tool_call.tool_name
        parameters = tool_call.parameters
        sender_role = getattr(tool_call, "sender_role", None)
        receiver_role = getattr(tool_call, "receiver_role", None)
        add_history({
            "event": "tool_call",
            "tool_name": tool_name,
            "sender": sender_role,
            "receiver": receiver_role,
            "params": parameters,
        })
        tool_key = f"{tool_name}:{str(parameters)}"
        if policy.is_duplicate(tool_name, parameters, queried_set):
            add_history({
                "event": "tool_call_skipped",
                "reason": "duplicate",
                "tool_name": tool_name,
                "params": parameters,
            })
            continue
        if policy.is_exceed_limit(tool_key, tool_call_count):
            add_history({
                "event": "tool_call_skipped",
                "reason": "exceed_limit",
                "tool_name": tool_name,
                "params": parameters,
            })
            continue
        tool_call_count, queried_set = policy.update_state(tool_name, parameters, tool_call_count, queried_set)
        new_tool_calls.append(tool_call)
    state["tool_call_count"] = tool_call_count
    state["queried_set"] = list(queried_set)
    state["tool_calls"] = new_tool_calls
    if new_tool_calls:
        add_history({"event": "tool_executor_triggered", "count": len(new_tool_calls)})
        return "tool_executor"
    add_history({"event": "quality_control_triggered"})
    return "quality_control"


def route_after_tools(state):
    # 兼容 dict 类型的 state
    def add_history(event):
        if isinstance(state, dict):
            state.setdefault("history", []).append(event)
        else:
            state.add_history(event)
    add_history({"event": "route_after_tools", "assigned_agent": state.get("assigned_agent")})
    return state.get("assigned_agent")


def route_after_complaint(state: AgentState):
    tool_calls = state.get("tool_calls", [])
    if tool_calls:
        state.add_history({"event": "complaint_tool_executor_triggered", "count": len(tool_calls)})
        return "tool_executor"
    state.add_history({"event": "complaint_quality_control_triggered"})
    return "quality_control"
