# PR 提交、触发 Review 的接口
# backend/app/api/v1/pr.py
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import Annotated
import asyncio
from app.api.deps import get_current_user
from app.services.github_client import github_client # 新增引入

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
    后台处理流程：拉取代码 -> AI 分析 -> 保存结果
    """
    print(f"\n[Worker] 开始处理任务，提取 PR 链接: {pr_url}")

    try:
        # 1. 真实拉取 GitHub Diff 代码
        print("[Worker] 正在向 GitHub 请求 Diff 数据...")
        diff_content = await github_client.get_pr_diff(pr_url)

        print(f"[Worker] ✅ 成功拉取到代码变更！Diff 长度: {len(diff_content)} 字符")
        print("------- Diff 预览 (前 300 字符) -------")
        print(diff_content[:300])
        print("---------------------------------------")

        # 2. (下一步目标) 将 diff_content 喂给 LangGraph AI 智能体
        print("[Worker] 准备启动 LangGraph 多 Agent 审查... (待实现)")

    except Exception as e:
        print(f"[Worker] ❌ 任务执行失败: {str(e)}")

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