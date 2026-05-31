# backend/app/agents/state.py
from typing import TypedDict, List, Annotated
import operator
from pydantic import BaseModel, Field


# --- Evaluate 节点输出的具体 Bug ---
class ReviewFinding(BaseModel):
    file_path: str = Field(description="出现问题的具体文件路径")
    line_number: str = Field(description="出现问题的行号或函数名")
    severity: str = Field(description="严重等级：critical, warning, info")
    description: str = Field(description="问题的具体描述，一句话概括")
    suggestion: str = Field(description="如何修改的具体建议")


#  新增：Synthesize 节点输出的全局评价模型
class CodeEvaluation(BaseModel):
    purpose: str = Field(description="这段 PR 变更的主要业务目的或功能是什么？（有什么用）")
    pros: List[str] = Field(
        description="代码的亮点与优点，例如：良好的设计模式、健壮的校验、性能优化等。如果没有可写'暂无明显亮点'")
    cons: List[str] = Field(description="宏观架构层面或代码规范上的缺点，例如：模块耦合度高、缺乏注释、扩展性差等")


class PRReviewState(TypedDict):
    pr_url: str
    diff_content: str

    is_trivial: bool
    skip_reason: str

    findings: Annotated[List[ReviewFinding], operator.add]

    #  新增全局评价字段
    evaluation: CodeEvaluation

    radar_scores: dict
    summary: str
    final_score: int