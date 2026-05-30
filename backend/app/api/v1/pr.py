# PR 提交、触发 Review 的接口
# backend/app/api/v1/pr.py
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Annotated
import asyncio
from app.api.deps import get_current_user

router = APIRouter()


# --- Pydantic 验证模型 ---
class PRSubmitRequest(BaseModel):
    github_pr_url: HttpUrl  # 使用强类型校验，防止前端乱传无效 URL


class ReviewResponse(BaseModel):
    task_id: str
    status: str
    message: str


# --- 模拟后台 AI 工作流 ---
async def process_pr_review_workflow(pr_url: str):
    """
    真正的 LangGraph AI 工作流会在这里执行。
    跑在后台任务中，不阻塞 API 响应。
    """
    print(f"[Worker] 开始拉取 PR 数据: {pr_url}")
    await asyncio.sleep(2)  # 模拟拉取耗时

    print("[Worker] RAG 上下文构建完毕，启动 LangGraph 多 Agent 审查...")
    await asyncio.sleep(3)  # 模拟大模型思考耗时

    print("[Worker] AI 评审完成，结果已存入数据库 / 推送回 Github！")


# --- 路由接口 ---
@router.post("/submit", response_model=ReviewResponse)
async def submit_pr_review(
        request: PRSubmitRequest,
        background_tasks: BackgroundTasks,
        current_user: Annotated[dict, Depends(get_current_user)]  # 只有登录用户才能提交
):
    """
    提交 GitHub PR 链接进行 AI 评审。接口会立即返回任务 ID。
    """
    # 将耗时的 AI 流程加入后台队列
    background_tasks.add_task(process_pr_review_workflow, str(request.github_pr_url))

    # 立即响应前端，前端可以凭借 task_id 去轮询状态或展示 Loading
    return ReviewResponse(
        task_id="task_8888_9999",
        status="processing",
        message="已成功将 PR 放入评审队列，AI 正在深度分析中..."
    )


@router.get("/{task_id}/status")
async def get_review_status(
        task_id: str,
        current_user: Annotated[dict, Depends(get_current_user)]
):
    """
    查询某次 AI 评审任务的当前状态与最终结果。
    """
    # Mock 数据，未来将从数据库读取
    return {
        "task_id": task_id,
        "status": "completed",
        "result": {
            "score": 85,
            "summary": "发现 2 处潜在的安全隐患，整体代码结构规范。",
            "details": []
        }
    }