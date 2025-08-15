# main.py
import json
import os

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from node.graph import graph_app, AgentState
from tools.knowledge_base_retriever_tool import KnowledgeBaseRetriever

app = FastAPI(title="电商虚拟客服团队 API")


class ChatRequest(BaseModel):
    message: str
    session_id: str


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
    kb_context = '\n'.join([r.get('content', str(r)) for r in kb_results if 'content' in r or r])
    # 构建新消息列表，裁剪上下文
    new_msgs = history_msgs + [HumanMessage(content=kb_context + '\n' + request.message)]
    new_msgs = AgentState.trim_context(new_msgs, max_length=10)
    initial_state = AgentState(
        messages=new_msgs,
        user_info=history.get('user_info', "") if history else "",
        assigned_agent=history.get('assigned_agent', "receptionist") if history else "receptionist",
        tool_calls=history.get('tool_calls', []) if history else [],
        tool_finished=history.get('sessions_finished', False) if history else False,
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
                        latest_msg = all_messages[-1]
                        if isinstance(latest_msg, AIMessage):
                            speak = latest_msg.content
                        else:
                            speak = latest_msg
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
