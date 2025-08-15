import gradio as gr
import requests
import json
import time
import uuid

# --- 后端 API 地址 ---
# 确保你的 FastAPI 后端正在运行，并且这个地址是正确的
BACKEND_URL = "http://127.0.0.1:8000/chat/stream"
SESSION_ID = f"gradio-session-{int(time.time())}"


def chat_function(message: str, history: list, user_id: int):
    session_id = None
    # 保证 history 只为 list of strings 或 dict，不插入 dict 到 history
    if history and isinstance(history, list) and len(history) > 0 and isinstance(history[0], dict):
        session_id = history[0].get('session_id')
        user_id = history[0].get('user_id', user_id)
    if not session_id:
        session_id = f"gradio-session-{uuid.uuid4()}"
    try:
        payload = {"message": message, "session_id": session_id, "user_id": user_id}
        response = requests.post(BACKEND_URL, json=payload, stream=True, timeout=300)
        response.raise_for_status()
        full_response = ""
        tool_info = ""
        if not response.content:
            return "抱歉，后端返回了空响应。"
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
                            elif data_json.get("type") == "tool_result":
                                tool_name = data_json.get('tool_name')
                                tool_content = str(data_json.get('content')).replace('\n', ' ')
                                tool_info = f"\n\n*调用工具 `{tool_name}`: {tool_content}*"
                        except json.JSONDecodeError:
                            pass
        if not full_response and not tool_info:
            return "（无文本回复）"
        return str(full_response + tool_info)
    except requests.exceptions.RequestException as e:
        return f"**错误**: 无法连接到后端服务。请确认服务正在运行，且地址正确。\n\n**详细信息**: {e}"
    except Exception as e:
        return f"**发生未知错误**: {e}"


# --- 创建并启动 Gradio 应用 ---
with gr.Blocks() as demo:
    gr.Markdown("# 🤖 电商客服 Chatbot (支持用户ID传入)")
    gr.Markdown("请输入用户ID进行测试：")
    user_id_input = gr.Number(label="用户ID", value=1, precision=0)
    user_info = gr.Markdown(f"当前用户ID：1")

    def update_user_info(user_id):
        return f"当前用户ID：{int(user_id)}"

    user_id_input.change(update_user_info, inputs=user_id_input, outputs=user_info)
    chat = gr.ChatInterface(
        fn=lambda message, history: chat_function(message, history, int(user_id_input.value)),
        title=None,
        description=None,
        examples=[
            ["你们的店铺支持七天无理由退货吗"],
            ["你好，我的订单ricecooker20250815002到哪了？"],
            ["你们一般使用什么快递公司发货？"],
            ["你好，我想查一下订单 n123qweqweqwewqe45 到哪里了"]
        ],
    )

if __name__ == "__main__":
    # 使用 share=True 可以创建一个临时的公网链接，方便分享
    demo.launch(share=False)
