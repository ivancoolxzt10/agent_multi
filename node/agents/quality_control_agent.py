from langchain_core.messages import AIMessage

from llm import llm
from node.agent_state import AgentState
from node.data_dto import ReplyResult
from node.utils import debug_handler


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
        final_summary_response = "感谢您的咨询，本次服务已结束。如果还有其他问题，欢迎随时联系我们！"

    # 确保 final_summary_response 是字符串
    if isinstance(final_summary_response, ReplyResult):
        # 假设 ReplyResult 有一个 `context` 属性，提取为字符串
        final_summary_response = final_summary_response.reply_context
    elif not isinstance(final_summary_response, str):
        # 如果不是字符串，强制转换为字符串
        final_summary_response = str(final_summary_response)

    # 将 AIMessage 添加到消息列表
    new_messages = messages + [AIMessage(content=final_summary_response)]

    # 返回更新后的状态，并标记对话结束
    return {
        "messages": [AIMessage(content=final_summary_response)],
        "conversation_finished": True,
        "all_messages": new_messages
    }
