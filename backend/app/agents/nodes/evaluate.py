import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from typing import List
from unidiff import PatchSet
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from app.agents.state import PRReviewState, ReviewFinding
from app.core.config import settings
from app.services.github_client import github_client


class FindingsList(BaseModel):
    items: List[ReviewFinding] = Field(description="审查发现的问题列表")


@tool
async def read_github_file(repo_name: str, file_path: str) -> str:
    """
    当你在审查代码 Diff 时，如果遇到未知的函数调用、不清楚的变量来源，或需要查看上下文，
    请调用此工具拉取该仓库中对应文件的完整源码。
    :param repo_name: 仓库全名，例如 "vuejs/core"
    :param file_path: 文件的相对路径，例如 "src/utils/index.ts"
    """
    return await github_client.get_file_content(repo_name, file_path, branch="main")


async def evaluate_single_file(llm, file_name: str, file_diff: str, repo_name: str, read_source_code: bool = True) -> \
List[ReviewFinding]:
    """使用纯 LangGraph 状态机构建的智能体循环"""

    # ==========================================
    # 阶段一：基于开关的推理模式选择
    # ==========================================
    if not read_source_code:
        # ⚡ 极速降级模式：不查源码，直接跳过 LangGraph 循环
        print(f"    ⚡ [LangGraph->Evaluate] 极速审查模式 (关闭查阅源码): {file_name} ...")
        analysis_text = f"请直接对以下代码变更（Diff）进行严格审查，找出潜在的安全漏洞、边界条件和性能瓶颈：\n{file_diff[:8000]}"

    else:
        # ⏳ 深度智能体模式：启动基于 LangGraph 的主动搜索
        print(f"    ⏳ [LangGraph->Evaluate] 启动状态机探索模式 (允许查阅源码): {file_name} ...")

        tools = [read_github_file]
        llm_with_tools = llm.bind_tools(tools)

        # 1. 定义思考节点
        async def call_model(state: MessagesState):
            messages = state["messages"]
            response = await llm_with_tools.ainvoke(messages)
            return {"messages": [response]}

        # 2. 构建 LangGraph 状态图
        workflow = StateGraph(MessagesState)

        # 添加节点与边
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", ToolNode(tools))
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", tools_condition)
        workflow.add_edge("tools", "agent")

        agent_app = workflow.compile()

        # 3. 运行状态机
        system_prompt = f"""你是一个拥有自主搜索能力的极客架构师。当前审查的仓库是：{repo_name}。
        请审查以下 Git Diff 文件片段。即使代码没有致命错误，也请尽量找出 1-2 个可以优化的地方，重点关注安全漏洞、边界条件和性能瓶颈。

        【重要授权】：如果 Diff 中的代码引用了外部的类、函数或变量（例如 import 语句），
        你有权力且必须调用 `read_github_file` 工具去查阅那个文件的源码！绝不允许在缺乏上下文时盲猜！
        查阅完毕后，综合 Diff 和你查到的上下文，写一份详细的审查分析草稿。"""

        initial_state = {
            "messages": [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"文件 [{file_name}] 的变更如下：\n{file_diff[:8000]}")
            ]
        }

        try:
            result_state = await agent_app.ainvoke(initial_state)
            analysis_text = result_state["messages"][-1].content
        except Exception as e:
            print(f"    ⚠️ [LangGraph->Evaluate] 探索阶段失败，降级为基础审查: {e}")
            analysis_text = f"基于以下代码变更进行审查发现：\n{file_diff[:8000]}"

    print(f"    💡 [LangGraph->Evaluate] {file_name} 推理完成，开始格式化提取...")

    # ==========================================
    # 阶段二：格式化输出 (Structured Extraction)
    # ==========================================
    parser = PydanticOutputParser(pydantic_object=FindingsList)

    format_prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个严格的数据格式化引擎。
        请将下面这份架构师的代码审查草稿，严格按照要求的 JSON 格式提取出来。

        ⚠️【绝对强制规范】：
        在你的 suggestion (修复建议) 字段中，如果包含了具体的代码修改示例，**必须且只能使用完整的 Markdown 代码块 (例如 ```typescript ...代码... ```) 来包裹！** 绝不允许将代码作为纯文本直接输出！

        \n{format_instructions}"""),
        ("user", "审查草稿内容：\n{analysis_text}")
    ]).partial(format_instructions=parser.get_format_instructions())

    format_chain = format_prompt | llm | parser

    try:
        # 提取最终数据
        result: FindingsList = await format_chain.ainvoke({"analysis_text": analysis_text})
        return result.items
    except Exception as e:
        print(f"    ❌ [LangGraph->Evaluate] 文件 {file_name} 格式化提取失败: {e}")
        return []


async def evaluate_node(state: PRReviewState) -> dict:
    """深度评估节点：采用 Map-Reduce 并发架构，按文件拆分进行独立审查。"""
    print("[Agent->Evaluate] 启动并发代码审查，解析 Diff 文件树...")

    if not settings.API_KEY:
        return {"findings": []}

    llm = ChatOpenAI(
        api_key=settings.API_KEY,
        base_url=settings.BASE_URL,
        model=settings.MODEL,
        temperature=0.1
    )

    diff_content = state.get("diff_content", "")
    pr_url = state.get("pr_url", "")

    # 🌟 从状态中读取开关参数（默认开启）
    read_source_code = state.get("read_source_code", True)

    repo_name = "unknown/repo"
    if pr_url:
        try:
            repo_info = github_client.parse_pr_url(pr_url)
            repo_name = f"{repo_info['owner']}/{repo_info['repo']}"
        except Exception:
            pass

    try:
        patch_set = PatchSet(diff_content)
    except Exception as e:
        print(f"⚠️ 解析 Diff 失败，降级为全文审查: {e}")
        # 🌟 透传开关参数
        findings = await evaluate_single_file(llm, "Unknown", diff_content, repo_name, read_source_code)
        return {"findings": findings}

    tasks = []
    for patched_file in patch_set:
        if patched_file.is_removed_file or patched_file.path.endswith('.md'):
            continue

        file_diff_text = str(patched_file)
        if len(file_diff_text.strip()) > 0:
            # 🌟 透传开关参数
            tasks.append(evaluate_single_file(llm, patched_file.path, file_diff_text, repo_name, read_source_code))

    if not tasks:
        return {"findings": []}

    print(f"🚀 [Agent->Evaluate] 共拆分出 {len(tasks)} 个有效文件，开启并行请求...")
    results = await asyncio.gather(*tasks)

    all_findings = []
    for file_findings in results:
        all_findings.extend(file_findings)

    return {"findings": all_findings}