# aftersales_tools.py
from langchain.tools import tool

from node.tools.knowledge_base_retriever_tool import knowledge_base_retriever


@tool
def get_order_details(order_id: str) -> dict:
    """获取指定订单号的详细信息，包括商品、金额、状态和收货地址。"""
    print(f"--- 售后工具: 获取订单详情 for {order_id} ---")
    if order_id == "n123qweqweqwewqe45":
        return {
            "order_id": "12345",
            "status": "已发货",
            "amount": 299.00,
            "items": [{"name": "蓝色连衣裙", "sku": "M码"}],
            "address": "上海市...",
        }
    return {"error": "未找到订单"}

@tool
def track_logistics(order_id: str) -> list:
    """跟踪指定订单号的物流轨迹。"""
    print(f"--- 售后工具: 跟踪物流 for {order_id} ---")
    if order_id == "n123qweqweqwewqe45":
        return [
            {"time": "2024-05-20 10:00", "status": "已揽收"},
            {"time": "2024-05-21 14:00", "status": "运输中"},
        ]
    return []

@tool
def initiate_return_process(order_id: str, item_sku: str, reason: str) -> str:
    """为指定订单的某个商品启动退货流程。"""
    print(f"--- 售后工具: 启动退货 for {order_id} ---")
    return f"已为订单 {order_id} 中的商品 {item_sku} 成功启动退货流程。退货地址将通过短信发送给您，请注意查收。"

aftersales_tool_list = [get_order_details, track_logistics, initiate_return_process,knowledge_base_retriever]

