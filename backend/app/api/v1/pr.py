# backend/app/api/v1/pr.py
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from unidiff import PatchSet
from langchain_community.callbacks import get_openai_callback
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.agents.graph import compile_review_graph
from app.services.github_client import github_client
from app.core.config import settings
from app.core.log_util import safe_print

router = APIRouter()


# ==========================================
# 阶段一：审查触发接口 (支持性能看板与功能扩展)
# ==========================================

class PRReviewRequest(BaseModel):
    pr_url: str = Field(..., description="GitHub Pull Request 的完整 HTML 链接")
    read_source_code: bool = Field(True, description="是否允许 AI 智能体主动拉取外部源码补全上下文")


@router.post("/review")
async def review_pr_manually(request: PRReviewRequest):
    """手动触发模式：并发执行 LangGraph 并返回完整结构化数据与消耗看板"""
    safe_print(f"\n[手动触发] 🔍 收到前端请求: {request.pr_url} (查阅源码: {request.read_source_code})")

    # 1. 设置 Token
    if hasattr(settings, "GITHUB_TOKEN") and settings.GITHUB_TOKEN:
        github_client.set_token(settings.GITHUB_TOKEN)

    # 2. 拉取基础 Diff
    try:
        diff_content = await github_client.get_pr_diff(request.pr_url)
        if not diff_content:
            raise HTTPException(status_code=400, detail="无法获取该 PR 的 Diff 内容")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"拉取 GitHub Diff 失败: {str(e)}")

    # 3. 解析新增文件列表
    added_files = []
    try:
        patch_set = PatchSet(diff_content)
        for patched_file in patch_set:
            if patched_file.is_added_file:
                added_files.append(patched_file.path)
    except Exception as e:
        safe_print(f"⚠️ 解析新增文件列表失败: {e}")

    initial_state = {
        "pr_url": request.pr_url,
        "diff_content": diff_content,
        "read_source_code": request.read_source_code,
    }

    # 4. 启动图并追踪性能与成本
    safe_print("[手动触发] 🤖 正在并发运行 LangGraph 状态机网络...")
    start_time = time.time()  # 🌟 开始计时

    try:
        graph_app = compile_review_graph()

        # 🌟 核心：使用回调拦截器包裹图的执行，完美捕获内部所有节点的 Token 消耗
        with get_openai_callback() as cb:
            result_state = await graph_app.ainvoke(initial_state)

        end_time = time.time()  # 🌟 结束计时
        elapsed_seconds = round(end_time - start_time, 2)

        # 🌟 成本估算防熔断逻辑：针对第三方模型如果不返回自带 cost 的情况做兜底计算
        cost = cb.total_cost
        if cost == 0:
            # 以近似 gpt-4o-mini 的计费标准作为参考: 输入 $0.15/1M, 输出 $0.60/1M
            cost = (cb.prompt_tokens / 1000000) * 0.15 + (cb.completion_tokens / 1000000) * 0.60

        safe_print(f"[看板数据] ⏱️ 耗时: {elapsed_seconds}s | 🪙 Tokens: {cb.total_tokens} | 💰 估算: ${cost:.4f}")

        evaluation = result_state.get("evaluation")
        if hasattr(evaluation, "model_dump"):
            evaluation = evaluation.model_dump()
        elif hasattr(evaluation, "dict"):
            evaluation = evaluation.dict()

        findings = result_state.get("findings", [])
        serialized_findings = [
            f.model_dump() if hasattr(f, "model_dump") else (f.dict() if hasattr(f, "dict") else f)
            for f in findings
        ]

        return {
            "status": "success",
            "is_trivial": result_state.get("is_trivial", False),
            "skip_reason": result_state.get("skip_reason", ""),
            "summary": result_state.get("summary", "AI 审查完成，未生成全局总结。"),
            "findings": serialized_findings,
            "final_score": result_state.get("final_score", 100),
            "radar_scores": result_state.get("radar_scores", {
                "security": 100, "performance": 100, "style": 100, "robustness": 100
            }),
            "evaluation": evaluation,
            "added_files": added_files,
            "usage_stats": {
                "elapsed_seconds": elapsed_seconds,
                "prompt_tokens": cb.prompt_tokens,
                "completion_tokens": cb.completion_tokens,
                "total_tokens": cb.total_tokens,
                "estimated_cost_usd": round(cost, 4)
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能体工作流执行失败: {str(e)}")


# ==========================================
# 阶段二：缺陷实时追问接口 (PR Chat)
# ==========================================

class PRChatRequest(BaseModel):
    file_path: str = Field(description="当前讨论的文件路径")
    code_snippet: str = Field(description="相关的代码片段或上下文 Diff")
    finding_description: str = Field(description="AI 之前给出的审查建议（缺陷描述）")
    user_message: str = Field(description="用户针对这个缺陷提出的疑问或反驳")


@router.post("/chat")
async def chat_about_finding(request: PRChatRequest):
    """
    缺陷双向互动接口：前端将具体的缺陷上下文发送过来，AI 针对性地进行解答
    """
    safe_print(f"\n[实时对话] 💬 收到用户针对 {request.file_path} 的提问...")

    if not settings.API_KEY:
        raise HTTPException(status_code=500, detail="未配置大模型 API_KEY")

    # 实例化一个轻量级的对话 LLM（温度可稍微调高，增加沟通的自然感）
    llm = ChatOpenAI(
        api_key=settings.API_KEY,
        base_url=settings.BASE_URL,
        model=settings.MODEL,
        temperature=0.4
    )

    # 组装极具极客风格的系统提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个资深且极具同理心的极客架构师。用户正在向你请教你之前做出的代码审查建议。

        【上下文信息】
        - 当前讨论的文件：{file_path}
        - 相关的原始代码：
        ```text
        {code_snippet}
        ```
        - 你之前给出的审查建议：
        > {finding_description}

        【你的任务】
        请以专业、耐心且直指核心的语气回答用户的疑问。
        如果用户指出你的建议有误或不适用，请结合代码重新分析，并虚心承认偏差。
        在给出新的修复方案时，必须使用 Markdown 代码块包裹。"""),
        ("user", "{user_message}")
    ])

    chain = prompt | llm

    try:
        response = await chain.ainvoke({
            "file_path": request.file_path,
            "code_snippet": request.code_snippet,
            "finding_description": request.finding_description,
            "user_message": request.user_message
        })

        reply = response.content
        if not isinstance(reply, str):
            reply = str(reply)

        return {
            "status": "success",
            "reply": reply
        }
    except Exception as e:
        safe_print(f"[实时对话] ❌ 聊天回复失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))