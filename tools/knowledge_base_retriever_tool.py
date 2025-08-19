from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from kg.embeddings import embeddings
import os
import time

def extract_qa_pairs(docs):
    qa_pairs = []
    seen_contents = set()
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
            content = doc.page_content.strip()
        elif question and answer:
            content = f"Q: {question}\nA: {answer}"
        elif question:
            content = f"Q: {question}"
        elif answer:
            content = f"A: {answer}"
        else:
            content = ""
        # 去重
        if content and content not in seen_contents:
            qa_pairs.append({
                "role": "tool",
                "content": content,
                "timestamp": int(time.time())
            })
            seen_contents.add(content)
    return qa_pairs

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
    qa_structured = extract_qa_pairs(retrieved_results)
    # 再次去重，保证输出唯一
    unique_structured = []
    seen_contents = set()
    for item in qa_structured:
        if item["content"] not in seen_contents:
            unique_structured.append(item)
            seen_contents.add(item["content"])
    knowledge_content = "\n\n".join([item["content"] for item in unique_structured])
    print(f"--- 知识库检索结果 (阈值 {threshold}): {knowledge_content} ---")
    # 判断会话是否结束：如果检索结果明确且与用户问题高度相关，则结束，否则继续
    can_reply_to_user = False
    if knowledge_content:
        end_keywords = ["已解决", "没有问题", "不需要", "谢谢", "本次会话已结束"]
        for kw in end_keywords:
            if kw in knowledge_content:
                can_reply_to_user = True
                break
        if len(retrieved_results) == 1 and len(knowledge_content) > 30:
            can_reply_to_user = True
    return {
        "role": "tool",
        "knowledge_base_result": unique_structured if unique_structured else [{"role": "tool", "content": "未找到相关信息。", "timestamp": int(time.time())}],
        "can_reply_to_user": can_reply_to_user
    }