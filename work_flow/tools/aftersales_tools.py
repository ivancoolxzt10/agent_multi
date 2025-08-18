# aftersales_tools.py
from langchain.tools import tool
import os
import sqlite3

from work_flow.tools.knowledge_base_retriever_tool import knowledge_base_retriever


def get_db_conn():
    db_path = os.path.join(os.path.dirname(__file__), '../../data/aftersales.db')
    return sqlite3.connect(db_path)


@tool
def get_order_details(user_id: int, order_id: str) -> dict:
    """获取指定用户的订单号的详细信息，包括商品、金额、状态和收货地址。"""
    print(f"--- 售后工具: 获取订单详情 for user {user_id}, order {order_id} ---")
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('''SELECT o.order_id, o.status, o.amount, a.address FROM orders o LEFT JOIN addresses a ON o.address_id=a.id WHERE o.order_id=? AND o.user_id=?''', (order_id, user_id))
    row = c.fetchone()
    if not row:
        conn.close()
        return {"error": "未找到订单或无权限"}
    c.execute('''SELECT name, sku FROM order_items WHERE order_id=?''', (order_id,))
    items = [{"name": name, "sku": sku} for name, sku in c.fetchall()]
    result = {"order_id": row[0], "status": row[1], "amount": row[2], "items": items, "address": row[3]}
    conn.close()
    return result


@tool
def track_logistics(user_id: int, order_id: str) -> list:
    """跟踪指定用户订单号的物流轨迹。"""
    print(f"--- 售后工具: 跟踪物流 for user {user_id}, order {order_id} ---")
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT 1 FROM orders WHERE order_id=? AND user_id=?', (order_id, user_id))
    if not c.fetchone():
        conn.close()
        return []
    c.execute('''SELECT time, status FROM logistics WHERE order_id=? ORDER BY time''', (order_id,))
    logs = [{"time": time, "status": status} for time, status in c.fetchall()]
    conn.close()
    return logs


@tool
def initiate_return_process(user_id: int, order_id: str, item_sku: str, reason: str) -> str:
    """为指定用户订单的某个商品启动退货流程。"""
    print(f"--- 售后工具: 启动退货 for user {user_id}, order {order_id} ---")
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT 1 FROM orders WHERE order_id=? AND user_id=?', (order_id, user_id))
    if c.fetchone():
        c.execute('INSERT INTO return_status (order_id, item_sku, status) VALUES (?, ?, ?)', (order_id, item_sku, '退货申请已提交，待审核'))
        conn.commit()
        conn.close()
        return f"已为订单 {order_id} 中的商品 {item_sku} 成功启动退货流程。退货地址将通过短信发送给您，请注意查收。"
    conn.close()
    return "订单号无效或无权限，无法启动退货流程。"


@tool
def initiate_refund_process(user_id: int, order_id: str, amount: float, reason: str) -> str:
    """为指定用户订单申请退款。"""
    print(f"--- 售后工具: 申请退款 for user {user_id}, order {order_id} ---")
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT 1 FROM orders WHERE order_id=? AND user_id=?', (order_id, user_id))
    if c.fetchone():
        c.execute('INSERT INTO refund_status (order_id, status) VALUES (?, ?)', (order_id, '退款申请已提交，待审核'))
        conn.commit()
        conn.close()
        return f"订单 {order_id} 已成功提交退款申请，金额 ¥{amount}，原因：{reason}。预计3-5个工作日到账。"
    conn.close()
    return "订单号无效或无权限，无法申请退款。"


@tool
def get_aftersales_policy() -> str:
    """查询平台售后政策。"""
    print("--- 售后工具: 查询售后政策 ---")
    return "本平台支持7天无理由退换货，部分特殊商品除外。退换货流程请参考帮助中心。"


@tool
def get_return_status(user_id: int, order_id: str, item_sku: str) -> dict:
    """查询指定用户订单的退换货进度。"""
    print(f"--- 售后工具: 查询退换货进度 for user {user_id}, order {order_id} ---")
    conn = get_db_conn()
    c = conn.cursor()
    c.execute('SELECT 1 FROM orders WHERE order_id=? AND user_id=?', (order_id, user_id))
    if not c.fetchone():
        conn.close()
        return {"order_id": order_id, "item_sku": item_sku, "status": "无权限或无订单"}
    c.execute('SELECT status FROM return_status WHERE order_id=? AND item_sku=? ORDER BY id DESC LIMIT 1', (order_id, item_sku))
    row = c.fetchone()
    status = row[0] if row else "无退换货记录"
    conn.close()
    return {"order_id": order_id, "item_sku": item_sku, "status": status}


@tool
def get_customer_service_contact() -> dict:
    """获取售后客服联系方式。"""
    print("--- 售后工具: 获取售后客服联系方式 ---")
    return {"phone": "400-800-1234", "email": "support@shop.com", "online": "www.shop.com/chat"}


aftersales_tool_list = [
    get_order_details,
    track_logistics,
    initiate_return_process,
    initiate_refund_process,
    get_aftersales_policy,
    get_return_status,
    get_customer_service_contact,
    knowledge_base_retriever,
]
