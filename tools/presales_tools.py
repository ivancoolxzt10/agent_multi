# presales_tools.py
import os
from langchain.tools import tool
from langchain_community.vectorstores import FAISS

from kg_tools.embeddings import embeddings
from tools.knowledge_base_retriever_tool import knowledge_base_retriever

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
def get_product_retriever_tool(query: str) -> list:
    """根据查询内容查找商品信息、店铺政策、活动规则等售前相关问题的答案。"""
    if not os.path.exists("../faiss_index"):
        raise FileNotFoundError("FAISS index not found. Run ingest.py first.")
    db = FAISS.load_local("../faiss_index", embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever()
    docs = retriever.get_relevant_documents(query)
    return [doc.page_content for doc in docs]

@tool
def check_stock(product_id: str, sku: str = None) -> dict:
    """检查指定商品ID和SKU的实时库存状态。"""
    print(f"--- 售前工具: 检查库存 for {product_id} (SKU: {sku}) ---")
    # 模拟库存查询
    if product_id == "p123":
        return {"product_id": "p123", "status": "有货", "stock_count": 150}
    elif product_id == "p456":
        return {"product_id": "p456", "status": "缺货", "stock_count": 0}
    return {"product_id": product_id, "status": "未找到商品", "stock_count": 0}

presales_tool_list = [get_product_retriever_tool, check_stock,knowledge_base_retriever,get_order_details]