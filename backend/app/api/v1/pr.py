# PR 提交、触发 Review 的接口
# backend/app/api/v1/pr.py
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel, HttpUrl,Field
from typing import Annotated
import asyncio
from app.api.deps import get_current_user
from app.services.github_client import github_client # 新增引入
from app.agents.graph import compile_review_graph

router = APIRouter()


# --- Pydantic 验证模型 ---
class PRSubmitRequest(BaseModel):
    # 使用 Field 注入真实可用的默认测试链接
    github_pr_url: HttpUrl = Field(
        ...,
        title="GitHub PR 链接",
        description="请填入需要审查的 GitHub PR 完整网址",
        examples=["https://github.com/vuejs/core/pull/9652"] # <--- 换成了 Vue 官方的真实 PR
    )

class ReviewResponse(BaseModel):
    task_id: str
    status: str
    message: str


# --- 模拟后台 AI 工作流 ---
async def process_pr_review_workflow(pr_url: str):
    """
    后台处理流程：拉取代码 -> 启动 LangGraph AI 分析 -> 保存结果
    """
    print(f"\n[Worker] 🟢 开始处理评审任务: {pr_url}")

    try:
        # 1. 真实拉取 GitHub Diff 代码
        print("[Worker] 正在向 GitHub 请求 Diff 数据...")
        diff_content = await github_client.get_pr_diff(pr_url)
        print(f"[Worker] ✅ 成功拉取代码，Diff 长度: {len(diff_content)} 字符")

        # 2. 初始化并启动 LangGraph 智能体网络
        print("[Worker] 🧠 启动 LangGraph 多 Agent 审查网络...")
        graph_app = compile_review_graph()

        # 构造初始状态 (注意：这里必须与最新的 PRReviewState 保持一致)
        initial_state = {
            "pr_url": pr_url,
            "diff_content": diff_content,
            "is_trivial": False,
            "skip_reason": "",
            "findings": [],  # <--- 使用了新的 findings 字段
            "radar_scores": {},
            "summary": "",
            "final_score": 0
        }

        # invoke 会按照我们在 graph.py 中定义的边，一步步执行节点
        final_state = graph_app.invoke(initial_state)

        # 3. 打印最终结果 (适配最新的状态数据结构)
        print("\n================ 评审结果报告 ================")
        print(f"🔹 最终得分: {final_state.get('final_score')} 分")  # 改为 final_score
        print(f"🔹 雷达图维度: {final_state.get('radar_scores')}")  # 新增雷达图打印
        print(f"🔹 整体总结: {final_state.get('summary')}")
        print(f"🔹 具体建议详情:")

        findings = final_state.get('findings', [])
        if not findings:
            print("   ✅ 未发现明显需要改进的地方。")
        else:
            for idx, finding in enumerate(findings):
                # finding 是我们在 evaluate.py 中强制大模型返回的 Pydantic 模型对象
                print(
                    f"   {idx + 1}. [{finding.severity.upper()}] 📍 文件: {finding.file_path} (行号/函数: {finding.line_number})")
                print(f"      描述: {finding.description}")
                print(f"      建议: {finding.suggestion}\n")
        print("============================================\n")

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