import gradio as gr
import requests
import json
import time
import uuid
import os

# --- 后端 API 地址 ---
# 确保你的 FastAPI 后端正在运行，并且这个地址是正确的
BACKEND_URL = "http://127.0.0.1:8000/chat/stream"

# 读取用户列表
users_path = os.path.join(os.path.dirname(__file__), 'data/users.json')
with open(users_path, encoding='utf-8') as f:
    USERS = json.load(f)
USER_OPTIONS = [f"{u['name']} (ID: {u['user_id']})" for u in USERS]
USER_ID_MAP = {f"{u['name']} (ID: {u['user_id']})": u['user_id'] for u in USERS}

def chat_function(message: str, history: list, user_select: str):
    """
    Gradio ChatInterface 的核心处理函数。
    支持每个会话唯一 session_id 和用户选择。
    """
    print(f"收到的消息: {message}")
    print(f"对话历史: {history}")
    print(f"当前用户选择: {user_select}")

    # 获取 user_id
    user_id = USER_ID_MAP.get(user_select, 1)  # 默认1号用户
    # 动态生成/提取 session_id 和 user_id
    if history and isinstance(history, list) and len(history) > 0 and isinstance(history[0], dict):
        session_id = history[0].get('session_id')
        user_id = history[0].get('user_id', user_id)
    else:
        session_id = f"gradio-session-{uuid.uuid4()}"
        history.insert(0, {'session_id': session_id, 'user_id': user_id})

    # Gradio ChatInterface 需要返回字符串而不是 dict
    # 只返回 assistant 的文本内容，不返回 dict 或 None
    # 下面的 yield 都只返回字符串
    try:
        payload = {"message": message, "session_id": session_id, "user_id": user_id}
        response = requests.post(
            BACKEND_URL,
            json=payload,
            stream=True,
            timeout=300,
        )
        response.raise_for_status()
        full_response = ""
        tool_info = ""
        if not response.content:
            yield "抱歉，后端返回了空响应。"
            return
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                chunk_str = chunk.decode('utf-8')
                for line in chunk_str.split('\n\n'):
                    if line.startswith("data:"):
                        data_part = line[5:].strip()
                        if data_part == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_part)
                            if data_json.get("type") == "speak":
                                full_response += data_json.get("content", "")
                                yield str(full_response + tool_info)
                            elif data_json.get("type") == "tool_result":
                                tool_name = data_json.get('tool_name')
                                tool_content = str(data_json.get('content')).replace('\n', ' ')
                                tool_info = f"\n\n*调用工具 `{tool_name}`: {tool_content}*"
                                yield str(full_response + tool_info)
                        except json.JSONDecodeError:
                            pass
        if not full_response and not tool_info:
            yield "（无文本回复）"
    except requests.exceptions.RequestException as e:
        print(f"请求异常: {e}")
        yield f"**错误**: 无法连接到后端服务。请确认服务正在运行，且地址正确。\n\n**详细信息**: {e}"
    except Exception as e:
        print(f"未知异常: {e}")
        yield f"**发生未知错误**: {e}"


# --- 创建并启动 Gradio 应用 ---
with gr.Blocks() as demo:
    gr.Markdown("# 🤖 多智能体电商客服 (Gradio版)")
    gr.Markdown("一个由 LangGraph 和通义千问驱动的虚拟客服团队。输入您的问题开始对话。\n\n请选择测试用户：")
    user_select = gr.Dropdown(label="选择用户", choices=USER_OPTIONS, value=USER_OPTIONS[0])
    chat = gr.ChatInterface(
        fn=lambda message, history: chat_function(message, history, user_select.value),
        title=None,
        description=None,
        examples=[
            ["你们的店铺支持七天无理由退货吗"],
            ["你好，我的订单 12345 到哪了？"],
            ["你们一般使用什么快递公司发货？"],
            ["你好，我想查一下订单 n123qweqweqwewqe45 到哪里了，当前的用户ivan"]
        ],
    )
    user_select.change(lambda x: None, inputs=user_select, outputs=None)  # 保证切换用户时刷新
    chat.render()

if __name__ == "__main__":
    demo.launch(share=False)