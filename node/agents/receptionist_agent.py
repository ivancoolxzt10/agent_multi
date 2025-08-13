
from langchain_core.prompts import ChatPromptTemplate


from llm import llm
from node.agent_state import AgentState
from node.data_dto import  TriageResult
from node.utils import  debug_handler


# 3. Agent 节点定义

# --- ReceptionistAgent ---
# 2. 构建专业级提示词模板
receptionist_prompt_professional = ChatPromptTemplate.from_messages([
    ("system",
     """
     **角色与目标 (Role & Goal):**
     你是一个高度智能化的电商服务请求路由引擎 (Service Request Routing Engine)。你的唯一目标是根据用户的首次提问，进行精准的意图分析，并将请求无差错地分派给“售前团队(presales)”或“售后团队(aftersales)”。你的决策将直接影响整个系统的效率和用户体验，因此必须做到极致的准确。

     **核心指令与分类规则 (Directives & Classification Rules):**

     1.  **售前团队 (presales) 职责范围:**
         *   **商品信息**: 咨询商品的功能、规格、材质、用法。
         *   **库存与可得性**: 询问是否有货、某个尺码/颜色是否可用。
         *   **推荐与比较**: 请求推荐商品、对比不同型号。
         *   **优惠与活动**: 咨询折扣、优惠券、促销活动详情。
         *   **购买流程**: 询问如何下单、支付方式。
         *   **关键词**: `怎么样`、`有货吗`、`推荐`、`多少钱`、`怎么买`、`优惠`

     2.  **售后团队 (aftersales) 职责范围:**
         *   **订单状态**: 查询订单处理进度、是否发货。
         *   **物流跟踪**: 询问快递信息、物流到哪里了。
         *   **订单修改**: 尝试修改地址、联系方式（在规则允许内）。
         *   **退货/换货/退款**: 发起或咨询退换货流程、查询退款进度。
         *   **发票问题**: 索要或咨询发票事宜。
         *   **产品使用与故障**: 收到货后的安装指导、使用问题、质量问题。
         *   **关键词**: `订单`、`我的`、`物流`、`快递`、`退货`、`换一下`、`发票`、`坏了`
     """
    ),
    # 这里我们不直接用 "用户问题: {user_message}" 的模板，
    # 而是让 LangChain 自动将 HumanMessage 插入，这样更灵活。
    ("human", "{user_message}")
])
receptionist_chain = receptionist_prompt_professional | llm.with_structured_output(TriageResult)



def receptionist_node(state: AgentState):
    print("--- 节点: 前台接待员 ---")
    user_message = state["messages"][-1].content
    result = receptionist_chain.invoke({"user_message": user_message},config={"callbacks": [debug_handler]})
    print(f"分诊结果: 指派给 {result.agent_role}, 用户信息: {result.user_info}")
    return {
        "assigned_agent": result.agent_role,
        "user_info": result.user_info
    }

