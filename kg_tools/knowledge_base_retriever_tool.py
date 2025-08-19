import os
import csv
import pickle
import numpy as np
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class KnowledgeBaseRetriever:
    def __init__(self):
        # 引入 embedding 模型
        from .embeddings import embeddings
        self.embeddings = embeddings

    def local_retrieve(self, query: str) -> Dict[str, Any]:
        results = []
        # FAQ 检索（TF-IDF+余弦相似度）
        # 算法说明：
        # 1. 使用 TfidfVectorizer 将 FAQ 问题和用户 query 转为向量。
        # 2. 计算 query 与每个 FAQ 问题的余弦相似度。
        # 3. 选取相似度最高的 top_n 个 FAQ。
        # 4. 设定相似度阈值，只有超过阈值的 FAQ 才会被返回。
        SIM_THRESHOLD = 0.2  # FAQ 相似度阈值，可根据实际情况调整
        faq_path = os.path.join(os.path.dirname(__file__), '../kg_data/faq.csv')
        faq_questions = []
        faq_answers = []
        if os.path.exists(faq_path):
            with open(faq_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    faq_questions.append(row.get('question', ''))
                    faq_answers.append(row.get('answer', ''))
            if faq_questions:
                # 向量化
                vectorizer = TfidfVectorizer().fit(faq_questions + [query])
                faq_vecs = vectorizer.transform(faq_questions)
                query_vec = vectorizer.transform([query])
                sims = cosine_similarity(query_vec, faq_vecs)[0]
                top_n = np.argsort(sims)[::-1][:3]  # 返回最相关的3条
                for idx in top_n:
                    if sims[idx] > SIM_THRESHOLD:
                        results.append({'content': faq_answers[idx], 'source': 'faq', 'score': float(sims[idx]), 'question': faq_questions[idx]})
        # FAISS 检索
        # 算法说明：
        # 1. 文档分割采用 RecursiveCharacterTextSplitter（见 ingest.py），将原始文档分割为多个片段。
        # 2. 每个片段用 embedding 模型转为向量，存入 FAISS 向量数据库。
        # 3. 检索时将 query 向量化，与 FAISS 索引做最近邻搜索，返回 top3。
        # 4. 设定 FAISS 检索分数阈值，只有分数高于阈值的片段才会被返回。
        FAISS_THRESHOLD = 0.2  # FAISS 检索分数阈值，可根据实际情况调整
        faiss_index_path = os.path.join(os.path.dirname(__file__), '../faiss_index/index.faiss')
        faiss_pkl_path = os.path.join(os.path.dirname(__file__), '../faiss_index/index.pkl')
        if os.path.exists(faiss_index_path) and os.path.exists(faiss_pkl_path):
            try:
                import faiss
                with open(faiss_pkl_path, 'rb') as f:
                    data = pickle.load(f)
                # 获取 FAISS 文本内容
                texts = [doc.page_content for doc in data[0]._dict.values()]
                # 用 embedding 模型向量化 query
                query_emb = np.array(self.embeddings.embed_query(query), dtype='float32').reshape(1, -1)
                # 加载 FAISS 索引
                index = faiss.read_index(faiss_index_path)
                D, I = index.search(query_emb, 3)  # top3
                for score, idx in zip(D[0], I[0]):
                    if idx >= 0 and score > FAISS_THRESHOLD:
                        results.append({'content': texts[idx], 'source': 'faiss', 'score': float(score)})
            except Exception as e:
                pass
        # 判断是否可以直接回复客户
        can_reply_to_user = bool(results)
        return {
            'role': 'tool',
            'knowledge_base_result': results if results else [{'content': '', 'source': 'faq'}],
            'can_reply_to_user': can_reply_to_user
        }

    def retrieve(self, query: str) -> Dict[str, Any]:
        return self.local_retrieve(query)
