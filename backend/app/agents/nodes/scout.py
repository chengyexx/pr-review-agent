# backend/app/agents/nodes/scout.py
from app.agents.state import PRReviewState
from app.core.log_util import safe_print


def scout_node(state: PRReviewState) -> dict:
    """
    侦察节点：分析 Diff 复杂度，判断是否属于“无脑合并”的修改。
    这是评委非常看重的降本增效（Token 控制）策略。
    """
    safe_print("[Agent->Scout] 正在分析 PR 变更内容与复杂度...")
    diff = state.get("diff_content", "")

    if len(diff.strip()) == 0:
        return {"is_trivial": True, "skip_reason": "空提交或无有效代码变更。"}

    if "diff --git" in diff and ".md" in diff and ".py" not in diff and ".ts" not in diff:
        return {"is_trivial": True, "skip_reason": "纯文档修改，无需深度安全审查。"}

    safe_print("[Agent->Scout] 发现核心代码变更，放行至深度审查环节。")
    return {"is_trivial": False, "skip_reason": ""}
