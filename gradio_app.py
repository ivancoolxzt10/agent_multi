import gradio as gr
import requests
import json
import time

# --- 后端 API 地址 ---
# 确保你的 FastAPI 后端正在运行，并且这个地址是正确的
BACKEND_URL = "http://127.0.0.1:8000/chat/stream"
SESSION_ID = f"gradio-session-{int(time.time())}"


def chat_function(message: str, history: list):
    """
    这是 Gradio ChatInterface 的核心处理函数。
    它接收用户消息和历史记录，并以流式方式返回 AI 的回复。
    """
    print(f"收到的消息: {message}")
    print(f"对话历史: {history}")

    # --- 核心改动：将整个逻辑包裹在 try...except 中，并确保 yield ---
    try:
        # 使用 with aiohttp.ClientSession() or httpx.AsyncClient() for async requests is better,
        # but for simplicity, we stick with requests in a sync function that Gradio will run in a thread.

        # 准备请求体
        payload = {"message": message, "session_id": SESSION_ID}

        # 发起流式请求
        response = requests.post(
            BACKEND_URL,
            json=payload,
            stream=True,
            timeout=300,
        )
        response.raise_for_status()  # 如果 HTTP 状态码不是 2xx，则抛出异常

        full_response = ""
        tool_info = ""

        # 检查响应是否有内容
        if not response.content:
            # 如果响应体为空，也要 yield 一些东西
            yield "抱歉，后端返回了空响应。"
            return  # 必须 return 来结束生成器

        # 迭代处理流式数据块
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                chunk_str = chunk.decode('utf-8')
                # SSE 消息以 "data:" 开头，并以 "\n\n" 结尾
                for line in chunk_str.split('\n\n'):
                    if line.startswith("data:"):
                        data_part = line[5:].strip()
                        if data_part == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_part)
                            # 根据后端返回的 JSON 结构进行处理
                            if data_json.get("type") == "speak":
                                full_response += data_json.get("content", "")
                                yield full_response + tool_info  # 流式返回
                            elif data_json.get("type") == "tool_result":
                                tool_name = data_json.get('tool_name')
                                tool_content = str(data_json.get('content')).replace('\n', ' ')
                                tool_info = f"\n\n*调用工具 `{tool_name}`: {tool_content}*"
                                yield full_response + tool_info
                        except json.JSONDecodeError:
                            # 忽略无法解析的行，可能是空行或注释
                            pass

        # 如果循环结束了，但什么都没 yield（例如，流中没有有效数据），
        # 我们在这里 yield 最终的 full_response 以避免错误。
        # 但在上面的逻辑中，每次 full_response 更新都会 yield，所以这里可能不会被执行。
        # 这是一个额外的保险。
        if not full_response and not tool_info:
            yield "（无文本回复）"


    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
        # **关键修复点**: 当发生任何网络错误时，捕获它并 yield 一条错误信息。
        # 这保证了即使在完全连接不上后端的情况下，生成器也至少 yield 了一次。
        yield f"**错误**: 无法连接到后端服务。请确认服务正在运行，且地址正确。\n\n**详细信息**: {e}"
    except Exception as e:
        print(f"未知异常: {e}")
        yield f"**发生未知错误**: {e}"


# --- 创建并启动 Gradio 应用 ---
demo = gr.ChatInterface(
    fn=chat_function,
    title="🤖 多智能体电商客服 (Gradio版)",
    description="一个由 LangGraph 和通义千问驱动的虚拟客服团队。输入您的问题开始对话。",
    examples=[["你们的店铺支持七天无理由退货吗"],["你好，我的订单 12345 到哪了？"],["你们一般使用什么快递公司发货？"], ["你好，我想查一下订单 n123qweqweqwewqe45 到哪里了，当前的用户ivan"]]
)

if __name__ == "__main__":
    # 使用 share=True 可以创建一个临时的公网链接，方便分享
    demo.launch(share=False)