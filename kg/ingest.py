# ingest.py
import os
import traceback

from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

from kg.embeddings import embeddings

load_dotenv()

def ingest_data():
    """
    加载、分割、向量化并存储知识库数据。
    """
    if not os.path.exists("faq.csv"):
        print("错误：faq.csv 文件未找到。")
        return

    print("开始灌输知识库...")

    # 1. 加载文档
    try:
        loader = CSVLoader(file_path="faq.csv", source_column="question", encoding="utf-8")
        documents = loader.load()
    except Exception as e:
        print("加载 faq.csv 时出错：", e)
        traceback.print_exc()
        return
    print(f"已加载 {len(documents)} 篇文档。")

    # 2. 分割文档
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = text_splitter.split_documents(documents)
    print(f"文档已分割为 {len(docs)} 个片段。")

    # 3. 创建向量数据库并存储
    print("正在创建并存储向量...")
    db = FAISS.from_documents(docs, embeddings)
    db.save_local("../faiss_index")
    print("知识库灌输完成，索引已保存到 'faiss_index' 目录。")

if __name__ == "__main__":
    ingest_data()


