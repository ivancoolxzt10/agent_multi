from langchain_core.tools import tool
from work_flow.tools.aftersales_tools import initiate_refund_process, get_aftersales_policy, get_return_status

@tool
def create_complaint_ticket(user_id: int, order_id: str, complaint_type: str, content: str) -> str:
    """创建投诉工单并返回工单号。"""
    import time
    ticket_id = f"T{int(time.time())}{user_id}"
    return f"投诉工单已创建，工单号：{ticket_id}，类型：{complaint_type}，内容：{content}"

@tool
def knowledge_base_retrieve(query: str) -> str:
    """根据投诉内容检索知识库FAQ，返回最相关的答案。"""
    import os, csv
    faq_path = os.path.join(os.path.dirname(__file__), '../../kg/faq.csv')
    best_answer = "未找到相关知识库答案。"
    if os.path.exists(faq_path):
        with open(faq_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if query in row.get('question', ''):
                    return row.get('answer', best_answer)
    return best_answer

complaint_tool_list = [
    create_complaint_ticket,
    initiate_refund_process,
    get_aftersales_policy,
    get_return_status,
    knowledge_base_retrieve
]
