# backend/app/agents/nodes/synthesize.py
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.agents.state import PRReviewState, CodeEvaluation
from app.core.config import settings
from app.core.log_util import safe_print


async def synthesize_node(state: PRReviewState) -> dict:
    """总结与打分节点：生成全局评价（优缺点/用途），并量化雷达图分数。"""
    safe_print("📊 [Agent->Synthesize] 正在调用大模型生成全局代码评估报告...")

    findings = state.get("findings", [])

    deductions = {"critical": 15, "warning": 5, "info": 2}
    total_deduction = sum(deductions.get(f.severity, 0) for f in findings)
    final_score = max(0, 100 - total_deduction)

    radar_scores = {
        "security": max(20, 100 - sum(15 for f in findings if f.severity == "critical")),
        "performance": max(20, 100 - sum(5 for f in findings if f.severity == "warning")),
        "style": max(20, 100 - sum(2 for f in findings if f.severity == "info")),
        "robustness": final_score
    }

    summary = f"本次审查共发现 {len(findings)} 个代码细节问题。综合得分为 {final_score} 分。"

    # 统一使用 API_KEY
    if not settings.API_KEY:
        mock_eval = CodeEvaluation(
            purpose="模拟评价：引入了新的用户登录鉴权模块。",
            pros=["代码结构清晰", "使用了强类型验证"],
            cons=["缺少核心函数的单元测试", "存在部分硬编码配置"]
        )
        return {"summary": summary, "radar_scores": radar_scores, "final_score": final_score, "evaluation": mock_eval}

    # 统一使用统一变量初始化大模型
    llm = ChatOpenAI(
        api_key=settings.API_KEY,
        base_url=settings.BASE_URL,
        model=settings.MODEL,
        temperature=0.3
    )

    parser = PydanticOutputParser(pydantic_object=CodeEvaluation)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一位资深的研发主管 (Tech Lead)。
            请根据以下代码变更内容，给出一个宏观的全局评估。
            1. 这段代码主要实现了什么功能？(purpose)
            2. 代码在架构、规范或实现思路上有什么优点？(pros)
            3. 宏观上看有什么缺点或隐患？(cons)
            \n{format_instructions}"""),
        ("user", "代码变更如下：\n{diff}")
    ]).partial(format_instructions=parser.get_format_instructions())

    # 拼装链条
    chain = prompt | llm | parser

    try:
        evaluation: CodeEvaluation = await chain.ainvoke({"diff": state["diff_content"][:8000]})
    except Exception as e:
        safe_print(f"⚠️ 全局评估生成失败: {e}")
        evaluation = CodeEvaluation(purpose="解析失败", pros=["无"], cons=["无"])

    return {
        "summary": summary,
        "radar_scores": radar_scores,
        "final_score": final_score,
        "evaluation": evaluation
    }