# AI PR Review Assistant
一个基于 LangGraph 与多 Agent 协同的智能代码审查引擎，旨在提升 Pull Request 的评审效率与代码质量。

# 项目概述
在现代软件开发流程中，Pull Request (PR) 评审是保障代码质量的关键环节，但往往耗时且容易遗漏深层逻辑问题。AI PR Review Assistant 通过引入多 Agent 协同架构（Scout-Evaluate-Synthesize），能够深度理解代码变更上下文，提供多维度的质量评分与外科手术式的修复建议，并将复杂的审查结果可视化。

# 核心特性
并行审查架构 (Map-Reduce)：采用并发协程处理大规模代码库变更，将 Diff 按文件拆分审查，大幅降低审查时延并彻底解决上下文截断问题。

多维质量评估：不仅指出 Bug，还利用 ECharts 生成安全性、性能、规范性、健壮性的多维雷达图，提供直观的质量感知。

架构师级全局视角：利用 LLM 对 PR 的业务目的进行语义分析，通过“优点”与“缺点”的对比，协助开发者快速识别架构级隐患。

强兼容性输出解析：采用 PydanticOutputParser 替代强绑定的 JSON Mode，支持无缝切换各种开源大模型，并强制通过 Markdown 规范输出，渲染出 Mac 终端风格的代码建议面板。

交互式反馈闭环：前端引入任务状态自动轮询机制，结合全屏 Loading 与平滑动画，提供媲美 SaaS 产品的流畅交互体验。

# 技术栈
后端: FastAPI (高性能 API), LangGraph (Agent 控制流), LangChain (LLM 编排), Unidiff (Diff 解析).

前端: Vue 3 (Composition API), Vite, Element Plus (组件库), ECharts (可视化), Pinia (状态管理).

智能核心: 支持 OpenAI API 或任意兼容 OpenAI 接口的本地/私有化 LLM。

快速开始
前端部署
Bash
cd frontend
npm install
npm run dev
后端部署
Bash
# 进入后端目录
cd backend
建议创建虚拟环境
python -m venv venv，
source venv/bin/activate  # Windows 下使用 venv\Scripts\activate，
pip install -r requirements.txt

# 配置环境变量 .env
API_KEY=your_key_here
BASE_URL=your_api_url

启动服务
uvicorn app.main:app --reload
# 架构设计
系统设计为基于状态机的工作流：

Scout Node：分析 PR 差异，识别核心业务模块，过滤冗余变更。

Evaluate Node：并发解析文件树，并行调用 LLM 执行针对性审查。

Synthesize Node：聚合各文件发现的问题，进行全局架构评估，量化雷达图评分。

🛣 未来演进 (Roadmap)
[ ] GitHub Webhook 集成：实现无感触发，自动在 GitHub PR 页面以行内评论（Inline Comment）形式提交 AI 审查意见。

[ ] RAG 知识库增强：引入向量数据库，检索项目历史文档与核心代码库，提供基于项目全局知识的审查建议。

传统静态分析协同：在 LangGraph 中集成 SonarQube 或 AST 扫描，将低级语法错误与逻辑语义错误解耦。

Human-in-the-Loop：支持开发者对 AI 评审结果进行标记（“误报/已采纳”），用于后续模型的强化学习（RLHF）微调。
