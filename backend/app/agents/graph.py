# backend/app/agents/graph.py
from langgraph.graph import StateGraph, END
from app.agents.state import PRReviewState
from app.agents.nodes.scout import scout_node
from app.agents.nodes.evaluate import evaluate_node
from app.agents.nodes.synthesize import synthesize_node


def route_after_scout(state: PRReviewState) -> str:
    """条件路由：根据 Scout 的判断决定去向"""
    if state.get("is_trivial"):
        return "synthesize"  # 如果是小修改，跳过审查，直接总结
    return "evaluate"  # 否则进入深度审查


def compile_review_graph():
    """
    组装并编译 LangGraph 工作流
    """
    # 实例化基于 Pydantic/TypedDict 的状态图
    workflow = StateGraph(PRReviewState)

    # 1. 注册节点 (从外部文件引入)
    workflow.add_node("scout", scout_node)
    workflow.add_node("evaluate", evaluate_node)
    workflow.add_node("synthesize", synthesize_node)

    # 2. 编排边与流转逻辑
    workflow.set_entry_point("scout")

    # 根据 Scout 的结果进行分流
    workflow.add_conditional_edges(
        "scout",
        route_after_scout,
        {"synthesize": "synthesize", "evaluate": "evaluate"}
    )

    # 深度审查结束后，汇入总结节点
    workflow.add_edge("evaluate", "synthesize")

    # 总结完成后，结束当前图
    workflow.add_edge("synthesize", END)

    # 编译成可执行的 Agent 实例
    return workflow.compile()