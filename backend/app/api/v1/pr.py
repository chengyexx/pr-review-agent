# backend/app/api/v1/pr.py
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel, HttpUrl, Field
from typing import Annotated
import uuid
import asyncio

from app.api.deps import get_current_user
from app.services.github_client import github_client
from app.agents.graph import compile_review_graph

router = APIRouter()

# 🌟【核心新增】：简易内存数据库，用于存放后台跑完的真实 AI 结果
REVIEW_TASKS = {}


# --- Pydantic 验证模型 ---
class PRSubmitRequest(BaseModel):
    github_pr_url: HttpUrl = Field(
        ...,
        title="GitHub PR 链接",
        description="请填入需要审查的 GitHub PR 完整网址",
        examples=["https://github.com/vuejs/core/pull/9652"]
    )


class ReviewResponse(BaseModel):
    task_id: str
    status: str
    message: str


# --- 后台真实 AI 工作流 ---
# 注意：接收 task_id 参数，以便跑完后将结果存入对应的字典
async def process_pr_review_workflow(task_id: str, pr_url: str):
    print(f"\n[Worker] 🟢 开始处理评审任务: {pr_url}")
    try:
        diff_content = await github_client.get_pr_diff(pr_url)
        graph_app = compile_review_graph()

        initial_state = {
            "pr_url": pr_url,
            "diff_content": diff_content,
            "is_trivial": False,
            "skip_reason": "",
            "findings": [],
            "radar_scores": {},
            "summary": "",
            "final_score": 0
        }

        # 真正调用 LangGraph 跑大模型
        final_state = await graph_app.ainvoke(initial_state)

        # 🌟【核心新增】：将大模型生成的真实结果，转换为前端需要的格式并保存
        REVIEW_TASKS[task_id] = {
            "status": "completed",
            "result": {
                "score": final_state.get('final_score', 100),
                "summary": final_state.get('summary', '审查完成'),
                "radar_scores": final_state.get('radar_scores',
                                                {"security": 100, "performance": 100, "style": 100, "robustness": 100}),
                # 兼容不同版本的 pydantic 转换
                "details": [f.model_dump() if hasattr(f, 'model_dump') else f.dict() for f in
                            final_state.get('findings', [])]
            }
        }
        print(f"[Worker] ✅ 任务 {task_id} 处理完毕并已保存！")

    except Exception as e:
        print(f"[Worker] ❌ 任务执行失败: {str(e)}")
        REVIEW_TASKS[task_id] = {"status": "failed", "message": str(e)}


# --- 路由接口 ---
@router.post("/submit", response_model=ReviewResponse)
async def submit_pr_review(
        request: PRSubmitRequest,
        background_tasks: BackgroundTasks,
        current_user: Annotated[dict, Depends(get_current_user)]
):
    # 1. 动态生成唯一的 Task ID
    task_id = f"task_{uuid.uuid4().hex[:8]}"

    # 2. 标记任务为处理中
    REVIEW_TASKS[task_id] = {"status": "processing"}

    # 3. 将任务丢入后台异步处理
    background_tasks.add_task(process_pr_review_workflow, task_id, str(request.github_pr_url))

    return ReviewResponse(
        task_id=task_id,
        status="processing",
        message="已成功将 PR 放入评审队列，AI 正在深度分析中..."
    )


@router.get("/{task_id}/status")
async def get_review_status(task_id: str, current_user: Annotated[dict, Depends(get_current_user)]):
    # 🌟【核心新增】：去内存数据库里查真实的进度
    task = REVIEW_TASKS.get(task_id)
    if not task:
        return {"status": "not_found", "message": "任务不存在"}
    return task