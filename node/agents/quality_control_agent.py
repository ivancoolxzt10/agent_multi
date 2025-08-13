from langchain_core.messages import AIMessage

from llm import llm
from node.agent_state import AgentState
from node.data_dto import  RepackResult
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

    # 这个 Prompt 是核心，它定义了LLM的角色、任务和语气
    prompt_template = f"""
    你是一名非常专业和友善的王牌客服。以下是你与一位客户的完整对话记录。
    你的任务是：
    1. 阅读并理解整个对话。
    2. 生成一段简短、友好、概括性的总结作为本次服务的结束语。
    3. 你的总结应该回顾客户的主要问题和我们给出的解决方案或答复。
    4. 最后，礼貌地结束对话，例如可以加上“感谢您的咨询，祝您生活愉快！”或类似的话。
    5. 直接输出总结内容，不要包含任何前缀，例如 "好的，这是您的总结："。

    对话记录:
    ---
    {chat_history_str}
    ---
    """
    receptionist_chain = prompt_template | llm.with_structured_output(RepackResult)
    try:
        # 直接调用 LLM，因为我们只需要纯文本回复
        final_summary_response = receptionist_chain.invoke({"user_message": prompt_template}, config={"callbacks": [debug_handler]})
        print(f"AI 生成的总结回复: {final_summary_response}")
    except Exception as e:
        print(f"!!! AI生成总结失败: {e}")
        # 设计降级策略：在AI调用失败时，返回一个通用的、安全的结束语
        final_summary_response = "感谢您的咨询，本次服务已结束。如果还有其他问题，欢迎随时联系我们！"

    # 3. 更新状态
    # 将AI生成的总结作为一条新的 "assistant" 消息添加到历史记录中
    new_messages = messages + [AIMessage(content=final_summary_response)]

    # 返回更新后的状态，并标记对话结束
    return {
        "messages": new_messages,
        "conversation_finished": True
    }

    return result