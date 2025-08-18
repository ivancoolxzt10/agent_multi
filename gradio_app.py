import gradio as gr
import requests
import json
import time
import uuid

# --- 后端 API 地址 ---
BACKEND_URL = "http://127.0.0.1:8000/chat/stream"


def chat_function(message: str, history: list, user_id: int, session_id: str):
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
    user_id_input.change(lambda uid: f"当前用户ID：{int(uid)}", inputs=user_id_input, outputs=user_info)

    chatbot = gr.Chatbot()
    message_box = gr.Textbox(label="请输入消息", placeholder="请输入您的问题...", lines=2)
    session_id_state = gr.State(str(uuid.uuid4()))
    history_state = gr.State([])
    send_btn = gr.Button("发送")
    clear_btn = gr.Button("清空对话并重置会话ID")

    def send_message(message, history, user_id, session_id):
        response = chat_function(message, history, int(user_id), session_id)
        # 更新历史
        history = history + [[message, response]]
        return history, "", history  # chatbot, 清空输入框, 更新history_state

    send_btn.click(
        send_message,
        inputs=[message_box, history_state, user_id_input, session_id_state],
        outputs=[chatbot, message_box, history_state]
    )

    def reset_session():
        return [], str(uuid.uuid4()), []  # 清空chatbot, 新session_id, 清空history

    clear_btn.click(
        reset_session,
        inputs=None,
        outputs=[chatbot, session_id_state, history_state]
    )

    # 示例对话
    gr.Markdown("## 示例问题：")
    gr.Markdown("""
    - 你们的店铺支持七天无理由退货吗
    - 你好，我的订单ricecooker20250815002到哪了？
    - 你们一般使用什么快递公司发货？
    - 你好，我想查一下订单 n123qweqweqwewqe45 到哪里了
    """)

if __name__ == "__main__":
    demo.launch(share=False)
