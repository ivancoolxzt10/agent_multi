# knowledge_tools.py
import os
from langchain.tools.retriever import create_retriever_tool
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool

from kg.embeddings import embeddings

@tool
def knowledge_base_retriever():
    """
    创建一个能够从企业知识库（FAQ）中检索信息的工具。
    """
    if not os.path.exists("faiss_index"):
        raise FileNotFoundError("FAISS index not found. Run ingest.py first.")

    db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever(search_kwargs={"k": 3})
    return create_retriever_tool(
        retriever,
        "knowledge_base_retriever",
        "当用户询问关于店铺政策（如退换货、发货时间）、产品通用信息（如材质、保养方法）、活动规则或其他无法通过API直接查询的常见问题时，使用此工具从知识库中查找答案。"
    )

