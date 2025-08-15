# main.py
import json
import os

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from node.graph import graph_app, AgentState
from tools.knowledge_base_retriever_tool import KnowledgeBaseRetriever

app = FastAPI(title="电商虚拟客服团队 API")


class ChatRequest(BaseModel):
    message: str
    session_id: str
    user_id: int


def format_sse(data: dict) -> str:
    """将字典格式化为 Server-Sent Event (SSE) 字符串。"""
    json_str = json.dumps(data, ensure_ascii=False)
    return f"data: {json_str}\n\n"


@app.post("/chat/stream")
async def stream_chat(request: ChatRequest):
    retriever = KnowledgeBaseRetriever()
    # 加载历史会话
    history = AgentState.load_state(request.session_id)
    history_msgs = history.get('messages', []) if history else []
    # 检索知识库（只用本地，不用 MCP）
    kb_results = retriever.retrieve(request.message)
    kb_context = '\n'.join([r.get('content', str(r)) for r in kb_results.get('knowledge_base_result', [])])
    # 构建新消息列表，裁剪上下文
    new_msgs = history_msgs.copy() if history_msgs else []
    # 如果没有历史消息，则添加当前用户输入
    if not history_msgs:
        new_msgs.append(HumanMessage(content=request.message))
    # 如果有知识库检索结果，则追加 ToolMessage
    if kb_context:
        new_msgs.append(ToolMessage(content=kb_context, tool_call_id="knowledge_base_retriever"))
    new_msgs = AgentState.trim_context(new_msgs, max_length=10)
    initial_state = AgentState(
        messages=new_msgs,
        user_id=str(request.user_id),  # 传递用户ID
        assigned_agent=history.get('assigned_agent', "receptionist") if history else "receptionist",
        tool_calls=history.get('tool_calls', []) if history else [],
        can_reply_to_user=kb_results.get('can_reply_to_user', False),
        called_tools=history.get('called_tools', {}) if isinstance(history.get('called_tools', {}), dict) else {},
        tool_call_count=history.get('tool_call_count', {}) if history else {},
        conversation_finished=False
    )
    async def event_stream():
        async for event in graph_app.astream_events(initial_state, version="v1"):
            kind = event["event"]
            node_name = event["name"]
            if kind == "on_chain_start":
                if event["name"] in ["receptionist", "presales", "aftersales", "tool_executor"]:
                    yield format_sse({
                        "type": "status",
                        "content": f"节点 '{event['name']}' 开始工作..."
                    })
            elif kind == "on_chain_end" :
                output = event["data"].get("output")
                if isinstance(output, dict) and output.get("conversation_finished"):
                    all_messages = output.get("all_messages", [])
                    if all_messages:
                        latest_msg = all_messages[-2]  # 获取倒数第二条消息
                        if isinstance(latest_msg, (AIMessage, ToolMessage)):
                            # 如果是 AIMessage 或 ToolMessage，提取内容
                            speak = getattr(latest_msg, 'content', str(latest_msg))
                            # ToolMessage 可能是 json字符串，需要解析
                            if isinstance(latest_msg, ToolMessage):
                                try:
                                    content_obj = json.loads(speak)
                                    # 优先提取 speak 字段，否则直接用原内容
                                    speak = content_obj.get('speak', speak)
                                except Exception:
                                    pass
                        else: # 如果不是 AIMessage 或 ToolMessage，直接使用内容
                            speak = str(latest_msg)
                        if not speak:
                            speak = "感谢您的咨询，本次服务已结束。如果还有其他问题，欢迎随时联系我们！"
                        yield format_sse({
                            "type": "speak",
                            "content": speak
                        })
                    # 保存会话状态
                    AgentState.save_state(request.session_id, output)
                    yield format_sse({"type": "done", "content": output.get("summary", "对话已结束。")})
                    break
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/")
def read_root():
    return {"message": "欢迎使用电商虚拟客服团队 API。"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
