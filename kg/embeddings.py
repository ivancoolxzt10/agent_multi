
from langchain_ollama import OllamaEmbeddings

embeddings = OllamaEmbeddings(
    model="mxbai-embed-large:latest",
    base_url="http://localhost:11434"  # 可选，默认即为此地址
)

print("✅ Embeddings (Ollama model: 'mxbai-embed-large:latest') initialized successfully.")