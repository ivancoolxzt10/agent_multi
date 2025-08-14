
import os
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool

from kg.embeddings import embeddings

def extract_qa_pairs(documents):
    """
    从 Document 对象中提取问答对，返回格式化的问答内容。
    """
    qa_pairs = []
    for doc in documents:
        question = ""
        answer = ""
        if "question:" in doc.page_content:
            question = doc.page_content.split("question:")[1].split("answer:")[0].strip()
        if "answer:" in doc.page_content:
            answer = doc.page_content.split("answer:")[1].strip()
        if question and answer:
            qa_pairs.append(f"Q: {question}\nA: {answer}")
    return "\n\n".join(qa_pairs)

@tool
def knowledge_base_retriever(query: str, threshold: float = 0.5):
    """
    创建一个能够从企业知识库（FAQ）中检索信息的工具，并根据阈值过滤结果。
    """
    if not os.path.exists("faiss_index"):
        raise FileNotFoundError("FAISS index not found. Run ingest.py first.")

    db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever(search_kwargs={"k": 1})

    # 使用 invoke 方法替代 get_relevant_documents
    retrieved_results = retriever.invoke(query)

    knowledge_content = extract_qa_pairs(retrieved_results)
    print(f"--- 知识库检索结果 (阈值 {threshold}): {knowledge_content} ---")
    # 设置 conversation_finished 标志
    return {
        "knowledge_base_result": f"知识库检索结果:\n{knowledge_content}" if knowledge_content else "未找到相关信息。",
        "tool_finished": bool(knowledge_content)  # 如果有内容则结束对话
    }