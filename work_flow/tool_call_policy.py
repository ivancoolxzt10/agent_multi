class ToolCallPolicy:
    """
    工具调用策略：去重、限流、优先级等，可扩展
    """
    def __init__(self, max_calls=3):
        self.max_calls = max_calls

    def is_duplicate(self, tool_name, parameters, queried_set):
        if tool_name == "knowledge_base_retriever":
            query = parameters.get("query")
            return query in queried_set
        return False

    def is_exceed_limit(self, tool_key, tool_call_count):
        return tool_call_count.get(tool_key, 0) >= self.max_calls

    def update_state(self, tool_name, parameters, tool_call_count, queried_set):
        tool_key = f"{tool_name}:{str(parameters)}"
        tool_call_count[tool_key] = tool_call_count.get(tool_key, 0) + 1
        if tool_name == "knowledge_base_retriever":
            query = parameters.get("query")
            queried_set.add(query)
        return tool_call_count, queried_set

