# e_commerce_cs_agent_poetry/llm.py
from langchain_ollama import ChatOllama
# 实例化一个指向本地 Ollama 服务的 ChatOllama 对象。
# LangChain 会自动连接到默认的 Ollama API 地址 (http://localhost:11434)。

# 如果你的 Ollama 服务运行在不同的地址或端口，你可以这样指定：
llm = ChatOllama(model="qwen3:1.7b", base_url="http://localhost:11434")

print(f"✅ LLM (Ollama model: 'qwen3:8b') initialized successfully.")