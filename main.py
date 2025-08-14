# main.py
import json

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from node.graph import graph_app, AgentState

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
    """
    与电商虚拟客服团队进行流式对话。
    使用 astream_events 提供更丰富的流式体验。
    """

    async def event_stream():
        initial_state = AgentState(
            messages=[HumanMessage(content=request.message)],
            user_info="",
            assigned_agent="receptionist",
            tool_calls=[],
            conversation_finished=False
        )

        # 使用 astream_events 来获取更详细的事件信息
        # version="v1" 是必需的，以使用标准事件格式
        async for event in graph_app.astream_events(initial_state, version="v1"):
            kind = event["event"]
            node_name = event["name"]
            # 当一个节点（Agent）开始工作时
            if kind == "on_chain_start":
                # 我们只关心我们定义的图节点的开始事件
                if event["name"] in ["receptionist", "presales", "aftersales", "tool_executor"]:
                    yield format_sse({
                        "type": "status",
                        "content": f"节点 '{event['name']}' 开始工作..."
                    })

            # 当一个节点（Agent）完成工作时
            elif kind == "on_chain_end" :
                output = event["data"].get("output")
                if isinstance(output, dict) and output.get("conversation_finished"):
                    all_messages = output.get("all_messages", [])
                    if all_messages:
                        latest_msg = all_messages[-1]
                        # 如果是 JSON 字符串，尝试解析
                        if isinstance(latest_msg, AIMessage):
                            speak = latest_msg.content  # 提取 content 属性
                        else:
                            # 如果不是 AIMessage，直接使用 latest_msg
                            speak = latest_msg
                        yield format_sse({
                            "type": "speak",
                            "content": speak
                        })
                    # 发送结束信号
                    yield format_sse({"type": "done", "content": output.get("summary", "对话已结束。")})
                    break


    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/")
def read_root():
    return {"message": "欢迎使用电商虚拟客服团队 API。"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
