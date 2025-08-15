from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from kg.embeddings import embeddings
import os

def extract_qa_pairs(docs):
    qa_pairs = []
    for doc in docs:
        question = ""
        answer = ""
        # 兼容多种格式，优先结构化
        if hasattr(doc, 'metadata') and doc.metadata:
            question = doc.metadata.get('question', '').strip()
            answer = doc.metadata.get('answer', '').strip()
        # 兼容原始文本格式
        if not question and "question:" in doc.page_content:
            question = doc.page_content.split("question:")[1].split("answer:")[0].strip()
        if not answer and "answer:" in doc.page_content:
            answer = doc.page_content.split("answer:")[1].strip()
        # 兼容无结构内容
        if not question and not answer:
            qa_pairs.append(doc.page_content.strip())
        elif question and answer:
            qa_pairs.append(f"Q: {question}\nA: {answer}")
        elif question:
            qa_pairs.append(f"Q: {question}")
        elif answer:
            qa_pairs.append(f"A: {answer}")
    return "\n\n".join(qa_pairs)

@tool
def knowledge_base_retriever(query: str, threshold: float = 0.5):
    """
    创建一个能够从企业知识库（FAQ）中检索信息的工具，并根据阈值过滤结果。
    """
    if not os.path.exists("faiss_index"):
        raise FileNotFoundError("FAISS index not found. Run ingest.py first.")

    db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever(search_kwargs={"k": 3})
    retrieved_results = retriever.invoke(query)
    knowledge_content = extract_qa_pairs(retrieved_results)
    print(f"--- 知识库检索结果 (阈值 {threshold}): {knowledge_content} ---")
    # 判断会话是否结束：如果检索结果明确且与用户问题高度相关，则结束，否则继续
    session_finished = False
    if knowledge_content:
        # 简单规则：如果内容包含常见结束语或FAQ已完全覆盖，则结束
        end_keywords = ["已解决", "没有问题", "不需要", "谢谢", "本次会话已结束"]
        for kw in end_keywords:
            if kw in knowledge_content:
                session_finished = True
                break
        # 如果检索结果只有一个且内容很完整，也可结束
        if len(retrieved_results) == 1 and len(knowledge_content) > 30:
            session_finished = True
    return {
        "knowledge_base_result": f"知识库检索结果:\n{knowledge_content}" if knowledge_content else "未找到相关信息。",
        "session_finished": session_finished
    }