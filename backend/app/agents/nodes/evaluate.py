# backend/app/agents/nodes/evaluate.py
import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List
from unidiff import PatchSet
from app.agents.state import PRReviewState, ReviewFinding
from app.core.config import settings


class FindingsList(BaseModel):
    items: List[ReviewFinding] = Field(description="审查发现的问题列表")


async def evaluate_single_file(llm, file_name: str, file_diff: str) -> List[ReviewFinding]:
    print(f"   ⏳ [Agent->Evaluate] 正在并行审查文件: {file_name} ...")

    parser = PydanticOutputParser(pydantic_object=FindingsList)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个资深、严谨的高级架构师。
        请审查以下 Git Diff 文件片段。即使代码没有致命错误，也请尽量找出 1-2 个可以优化的地方。
        重点关注：
        1. 安全漏洞与边界条件（空指针、未处理异常等）。
        2. 性能瓶颈与代码可读性优化。
        \n{format_instructions}"""),
        ("user", "文件 [{file_name}] 的变更如下：\n{diff}")
    ]).partial(format_instructions=parser.get_format_instructions())


    chain = prompt | llm | parser

    try:
        result: FindingsList = await chain.ainvoke({"file_name": file_name, "diff": file_diff[:8000]})
        return result.items
    except Exception as e:
        print(f"[Agent->Evaluate] 文件 {file_name} 解析失败: {e}")
        return []


async def evaluate_node(state: PRReviewState) -> dict:
    """深度评估节点：采用 Map-Reduce 并发架构"""
    print("[Agent->Evaluate] 启动并发代码审查，解析 Diff 文件树...")

    # 统一使用 API_KEY
    if not settings.API_KEY:
        print("未检测到 API_KEY，返回模拟的审查问题。")
        mock_finding = ReviewFinding(
            file_path="src/main.ts", line_number="42", severity="warning",
            description="模拟问题：未处理的 Promise 异常", suggestion="建议添加 catch 块。"
        )
        return {"findings": [mock_finding]}

    # 统一使用统一变量初始化大模型
    llm = ChatOpenAI(
        api_key=settings.API_KEY,
        base_url=settings.BASE_URL,
        model=settings.MODEL,
        temperature=0.1
    )

    diff_content = state.get("diff_content", "")

    try:
        patch_set = PatchSet(diff_content)
    except Exception as e:
        print(f"⚠️ 解析 Diff 失败，降级为全文审查: {e}")
        findings = await evaluate_single_file(llm, "Unknown", diff_content)
        return {"findings": findings}

    tasks = []
    for patched_file in patch_set:
        if patched_file.is_removed_file or patched_file.path.endswith('.md'):
            continue

        file_diff_text = str(patched_file)
        if len(file_diff_text.strip()) > 0:
            tasks.append(evaluate_single_file(llm, patched_file.path, file_diff_text))

    print(f"🚀 [Agent->Evaluate] 共拆分出 {len(tasks)} 个有效文件，开启并行请求...")
    if not tasks:
        return {"findings": []}

    results = await asyncio.gather(*tasks)

    all_findings = []
    for file_findings in results:
        all_findings.extend(file_findings)

    return {"findings": all_findings}