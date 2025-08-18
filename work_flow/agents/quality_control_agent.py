from langchain_core.messages import AIMessage

from llm import llm
from work_flow.agent_state import AgentState
from work_flow.data_dto import ReplyResult
from work_flow.utils import debug_handler


# --- QualityControlAgent (简化) ---
def quality_control_node(state: AgentState):
    print("--- 节点: 质检总结员 ---")

    # 1. 准备输入
    # 获取完整的对话历史
    messages = state["messages"]
    # 将消息列表格式化为对LLM友好的字符串
    chat_history_str = "\n".join([f"{msg.type.capitalize()}: {msg.content}" for msg in messages])

    # 2. 设计 Prompt 并调用 LLM
    print("正在调用AI生成最终总结回复...")

    # 定义完善客服回复内容的 Prompt 模板
    prompt_template = """
    你是一名专业且友善的电商客户服务质量审查员。以下是客服的回复内容：
    ---
    {chat_history_str}
    ---
    你的任务是：
    1. 仔细阅读客服的回复内容，判断是否存在问题或需要优化的地方。
    2. 如果回复内容存在问题或可以优化，请重新修改并提供更完善的回复。
    3. 如果回复内容没有问题且无需修改，请直接输出原话。
    4. 确保最终回复内容简洁、专业且友好，语气礼貌且体现责任感。
    5. 直接输出最终的回复内容，不需要任何前缀或额外说明。
    6. 请根据对话内容，判断本次会话是否可以直接回复客户。如果你认为用户的问题已全部解决，或用户明确表示无需继续，请在结构化输出中返回 can_reply_to_user: true，否则为 false。
    """

    try:
        # 构建带结构化输出的链
        formatted_prompt = prompt_template.format(chat_history_str=chat_history_str)
        # 调用 LLM 时直接传递字符串
        final_summary_response = llm.with_structured_output(ReplyResult).invoke(
            formatted_prompt,  # 确保这里是字符串
            config={"callbacks": [debug_handler]}
        )
        print(f"AI生成的总结: {final_summary_response}")
    except Exception as e:
        print(f"!!! AI生成总结失败: {e}")
        # 设计降级策略：在AI调用失败时，返回一个通用的、安全的结束语
        final_summary_response = ReplyResult(reply_context="感谢您的咨询，本次服务已结束。如果还有其他问题，欢迎随时联系我们！", can_reply_to_user=True)

    # 确保 final_summary_response 是 ReplyResult
    if isinstance(final_summary_response, ReplyResult):
        reply_text = final_summary_response.reply_context
        can_reply_to_user = getattr(final_summary_response, "can_reply_to_user", False)
    else:
        reply_text = str(final_summary_response)
        can_reply_to_user = False

    # 将 AIMessage 添加到消息列表
    new_messages = messages + [AIMessage(content=reply_text)]
    # 可在主流程中根据 session_finished 做后续处理

    # 只保留最后一轮问答：客户的问+最终AI回复
    # 找到最后一个 HumanMessage
    last_human = None
    for msg in reversed(messages):
        if getattr(msg, 'type', None) == 'human' or msg.__class__.__name__ == 'AIMessage':
            last_human = msg
            break
    # 构造只包含最后一问一答的消息列表
    if last_human:
        filtered_messages = [last_human, AIMessage(content=reply_text)]
    else:
        filtered_messages = [AIMessage(content=reply_text)]

    # 返回更新后的状态，并标记对话结束
    return {
        "messages": filtered_messages,
        "conversation_finished": can_reply_to_user,
        "all_messages": new_messages,
        "assigned_agent": state["assigned_agent"],
    }
