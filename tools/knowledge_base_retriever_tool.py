import os
import json
import csv
import pickle
import numpy as np
import faiss
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class KnowledgeBaseRetriever:
    def __init__(self):
        pass

    def local_retrieve(self, query: str) -> List[Dict[str, Any]]:
        results = []
        # FAQ 检索（TF-IDF+余弦相似度）
        faq_path = os.path.join(os.path.dirname(__file__), '../kg/faq.csv')
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
                    if sims[idx] > 0:
                        results.append({'content': faq_answers[idx], 'source': 'faq', 'score': float(sims[idx]), 'question': faq_questions[idx]})
        # FAISS 检索
        faiss_index_path = os.path.join(os.path.dirname(__file__), '../faiss_index/index.faiss')
        faiss_pkl_path = os.path.join(os.path.dirname(__file__), '../faiss_index/index.pkl')
        if os.path.exists(faiss_index_path) and os.path.exists(faiss_pkl_path):
            try:
                with open(faiss_pkl_path, 'rb') as f:
                    data = pickle.load(f)
                # 检查 embeddings 维度
                if 'embeddings' in data and hasattr(data['embeddings'], 'shape'):
                    emb_dim = data['embeddings'].shape[1]
                    # 这里假设有一个 get_query_embedding 方法，或用第一个 embedding 维度填充
                    # 推荐：实际项目应用真实 embedding 方法
                    query_vec = np.zeros((1, emb_dim), dtype='float32')
                    # TODO: 替换为真实 embedding 生成逻辑
                    # index = faiss.read_index(faiss_index_path)
                    # D, I = index.search(query_vec, k=3)
                    # for idx in I[0]:
                    #     if idx < len(data['texts']):
                    #         results.append({'content': data['texts'][idx], 'source': 'faiss'})
                # 如果没有 embedding 信息，则跳过 FAISS 检索
            except Exception as e:
                # FAISS 检索异常时只返回 FAQ 结果
                pass
        return results

    def retrieve(self, query: str) -> List[Dict[str, Any]]:
        # 只用本地检索，不用 MCP
        return self.local_retrieve(query)
