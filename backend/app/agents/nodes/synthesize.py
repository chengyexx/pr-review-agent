# backend/app/agents/nodes/synthesize.py
from app.agents.state import PRReviewState


def synthesize_node(state: PRReviewState) -> dict:
    """
    总结与打分节点：将所有的 findings 进行量化，生成雷达图数据与最终总结。
    """
    print("📊 [Agent->Synthesize] 正在汇总数据并生成雷达图评分...")

    if state.get("is_trivial"):
        return {
            "summary": f"✅ 本次 PR 为常规/琐碎修改（原因：{state.get('skip_reason')}）。LGTM！",
            "radar_scores": {"security": 100, "performance": 100, "style": 100, "robustness": 100},
            "final_score": 100
        }

    findings = state.get("findings", [])

    if not findings:
        return {
            "summary": "✅ 代码质量极高，未发现明显的安全与性能风险。LGTM！",
            "radar_scores": {"security": 98, "performance": 95, "style": 95, "robustness": 96},
            "final_score": 96
        }

    # 简单的扣分逻辑 (演示用)
    deductions = {"critical": 15, "warning": 5, "info": 2}
    total_deduction = sum(deductions.get(f.severity, 0) for f in findings)

    final_score = max(0, 100 - total_deduction)

    # 模拟雷达图各维度评分计算
    radar_scores = {
        "security": max(20, 100 - sum(15 for f in findings if f.severity == "critical")),
        "performance": max(20, 100 - sum(5 for f in findings if f.severity == "warning")),
        "style": max(20, 100 - sum(2 for f in findings if f.severity == "info")),
        "robustness": final_score
    }

    summary = f"⚠️ 本次审查共发现 {len(findings)} 个潜在问题。其中包含 " \
              f"{sum(1 for f in findings if f.severity == 'critical')} 个严重风险。请核对具体建议。"

    return {
        "summary": summary,
        "radar_scores": radar_scores,
        "final_score": final_score
    }