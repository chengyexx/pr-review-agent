# backend/app/agents/nodes/evaluate.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List
from app.agents.state import PRReviewState, ReviewFinding
from app.core.config import settings


# 为了让大模型一次性返回多个 finding，我们在内部包装一个 List 模型
class FindingsList(BaseModel):
    items: List[ReviewFinding] = Field(description="审查发现的问题列表")


def evaluate_node(state: PRReviewState) -> dict:
    print("🧠 [Agent->Evaluate] 启动深度代码审查，提取结构化特征...")

    if not settings.API_KEY:
        print("⚠️ 未检测到 API_KEY，返回模拟的审查问题。")
        mock_finding = ReviewFinding(
            file_path="src/main.ts", line_number="42", severity="warning",
            description="模拟问题：未处理的 Promise 异常", suggestion="建议添加 catch 块或使用 try-catch。"
        )
        return {"findings": [mock_finding]}

    llm = ChatOpenAI(
        api_key=settings.API_KEY,
        base_url=settings.BASE_URL,  # <--- 之前这里写成了 BASE_BASE
        model=settings.MODEL,
        temperature=0.1
    )

    # 核心魔法：强制大模型输出符合 Pydantic 定义的 JSON
    structured_llm = llm.with_structured_output(FindingsList)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个资深、严谨的高级后端/前端架构师。
        请审查以下 Git Diff。重点关注：
        1. 潜在的安全漏洞（SQL注入、XSS、越权等）。
        2. 性能瓶颈（如 N+1 查询、死循环、内存泄漏）。
        3. 代码健壮性与边界条件处理。
        不要提出类似于'增加注释'这种无聊的建议。如果你认为代码完美，返回空列表。"""),
        ("user", "代码变更如下：\n{diff}")
    ])

    chain = prompt | structured_llm

    try:
        # 为了防止过长，这里取前 5000 字符。进阶版可拆分多个 Chunk 并发审查。
        result: FindingsList = chain.invoke({"diff": state["diff_content"][:5000]})
        return {"findings": result.items}
    except Exception as e:
        print(f"❌ 大模型解析失败: {e}")
        return {"findings": []}