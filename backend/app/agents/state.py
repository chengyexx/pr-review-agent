# backend/app/agents/state.py
from typing import TypedDict, List, Annotated
import operator
from pydantic import BaseModel, Field


# --- 定义大模型强制输出的 Pydantic 数据结构 ---
class ReviewFinding(BaseModel):
    file_path: str = Field(description="出现问题的具体文件路径")
    line_number: str = Field(description="出现问题的行号或函数名（如无法确定行号填函数名）")
    severity: str = Field(description="严重等级：critical(致命风险), warning(警告), info(优化建议)")
    description: str = Field(description="问题的具体描述，一句话概括")
    suggestion: str = Field(description="如何修改的具体建议或代码片段")


class PRReviewState(TypedDict):
    """
    LangGraph 全局状态机，贯穿整个审查生命周期
    """
    pr_url: str
    diff_content: str

    # Scout 节点写入
    is_trivial: bool
    skip_reason: str

    # Evaluate 节点写入 (使用 operator.add 支持多 Agent 并发写入时结果累加)
    findings: Annotated[List[ReviewFinding], operator.add]

    # Synthesize 节点写入
    radar_scores: dict  # 雷达图多维评分 {"security": 90, "performance": 85, "style": 95}
    summary: str
    final_score: int