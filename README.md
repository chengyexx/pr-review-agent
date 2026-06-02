# AI-POWERED CODE REVIEW (智能代码评审助手)

**一个懂业务上下文、抗幻觉、极速响应的 GitHub Pull Request 智能评审流引擎。**

基于 LangGraph 与多 Agent 协同架构，旨在将开发者从繁琐的代码规范审查中解放出来，让团队的 Code Review 更加专注、高效、有深度。

---

## 真实需求洞察

在现代软件工程中，Code Review 是一项昂贵但必要的活动。我们深刻理解开发者在日常 PR 评审中的三大痛点：

* **上下文缺失（Context Loss）**：传统静态分析工具只懂语法，不懂业务；而直接喂给普通大模型的 Diff 往往因为缺乏上下文而产生“幻觉”。
* **误报疲劳（False Positive Fatigue）**：如果 AI 总是报告低价值的格式问题或不准确的“漏洞”，开发者会迅速对工具失去信任。
* **心智负担（Cognitive Load）**：审查几千行变更、跨越数十个文件的 PR 令人心力交瘁，评审往往流于形式（LGTM）。

**本项目正是为了打破这一僵局而生。**

---

## 核心功能与使用体验

本系统不仅提供了强大的 AI 分析内核，更倾注了大量精力在 **开发者体验 (DX)** 上：

* **PR 变更全局总结**：提炼变更意图，总结代码亮点与宏观架构不足。
* **多维质量雷达图**：量化评估 PR 的安全性、性能、规范度、健壮性，提供直观的代码健康度感知。
* **风险代码精准狙击**：深入代码行（Line-level），指出安全漏洞（如空指针、注入风险）与性能瓶颈。
* **沉浸式交互体验**：告别枯燥的纯文本报告。前端采用深色界面，包含多个模块。

---

## 核心架构与设计思考

为了满足严苛的生产环境要求，本系统在架构设计上做出了以下关键取舍与突破：

### 1. 上下文获取与理解 (Context Retrieval)
* **现状挑战**：Git Diff 只有增删的行，缺乏完整的类或函数定义。大段塞入 LLM 极易触发上下文截断。
* **设计思路**：采用 Unidiff 解析底层 PatchSet，将 PR 按文件粒度进行精准切片。对于每个文件，我们不只传入 Diff，还通过预处理补充必要的上下文。这使得 Agent 能够聚焦单个文件的深度语义，而非在庞大的全局 Diff 中迷失。

### 2. 分析准确性与误报/漏报控制 (Precision & Recall)
* **系统化提示词工程**：在 System Prompt 中注入了极为严苛的高级架构师审查准则，并强制要求仅对“安全、性能、边界条件”发声，刻意忽略无价值的格式问题（交给 ESLint 等工具）。
* **格式稳定性控制**：引入 LangChain 的 PydanticOutputParser 并结合前端“防御性正则解析 + CSS 兜底”，彻底解决 LLM 输出复杂 Markdown 容易导致的格式崩塌问题，保障 100% 的渲染成功率。
* **低温度采样**：将大模型 temperature 设定为 0.1，剥离模型的“创造力”，最大化其在代码审查场景下的“确定性与逻辑严密性”。

### 3. 响应速度优化 (Performance Optimization)
* **Map-Reduce 并发架构**：摒弃了串行审查的低效模式。在 LangGraph 的 Evaluate 节点中，利用 Python asyncio.gather 开启高并发协程。无论 PR 包含 5 个文件还是 50 个文件，审查耗时均收敛于最慢的单个文件响应时间，实现了极速响应。
* **前后端异步解耦**：后端引入 BackgroundTasks，前端采用基于定时器的短轮询（Polling）机制，避免了长连接超时，极大提升了系统的吞吐量与用户体验。

### 4. 模型选择策略 (Model Selection)
* **解耦与兼容**：系统不绑定单一模型生态。通过 langchain-openai 规范化接口，支持无缝切换 OpenAI (GPT-4o)、Anthropic (Claude 3.5 Sonnet) 甚至本地部署的开源模型（如 DeepSeek-Coder、Qwen）。
* **按需路由（未来演进）**：设计上支持在 Scout（侦察）节点使用快速廉价模型进行分发，在 Evaluate（评估）节点调用顶级推理模型进行深度审查，实现成本与智力的最佳平衡。

---

## 快速开始

### 1. 克隆与后端环境准备
```bash
git clone [https://github.com/your-username/pr-review-agent.git](https://github.com/your-username/pr-review-agent.git)
cd pr-review-agent/backend

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置 .env 文件 (配置你的 API_KEY 与 BASE_URL)
uvicorn app.main:app --reload
```

### 2. 前端环境准备
```bash
cd ../frontend
npm install
npm run dev
```
打开浏览器访问 `http://localhost:5173` 即可体验。

---

## 未来扩展方向 (Future Roadmap)

本系统在设计初衷即预留了强大的扩展接口，下一步演进方向如下：

* **RAG 增强上下文注入**：引入 FAISS 向量数据库。在审查 PR 时，先检索项目全局代码库与 CONTRIBUTING.md（团队规范），解决跨文件依赖调用的“盲视”问题，实现基于团队独有上下文的精准评审。
* **GitHub Webhook 全自动化集成**：无需手动输入 URL。与 GitHub App 深度集成，开发者创建 PR 后，AI 自动触发并在代码行间（Inline Comment）留下审查意见，实现工作流 100% 隐形嵌入。
* **混合审查管线 (Hybrid Pipeline)**：在 Agent 流中集成静态代码分析工具（如 SonarQube、AST 解析器），让传统工具负责基础底线，让大模型聚焦业务逻辑，形成双重保险。
* **Human-in-the-Loop (人类反馈学习)**：支持开发者在前端对 AI 意见点击“采纳”或“误报”，沉淀的纠偏数据将用于后续企业私有模型的 SFT（监督微调），让 AI 越用越懂团队代码库。

---

## 项目演示

**演示视频**：
# 最新视频↓
[点击这里观看 AI PR Review Assistant 完整功能介绍](【七牛云 x XENGINEER 暑期实训营-题目三】 https://www.bilibili.com/video/BV1QSV66MEUr/?share_source=copy_web&vd_source=dbbde7a85366f1693f082df34280afcd)


旧视频：[点击这里观看 AI PR Review Assistant 完整功能介绍]( https://www.bilibili.com/video/BV1w8VQ6QEeM/?share_source=copy_web&vd_source=dbbde7a85366f1693f082df34280afcd)

> *Built with Vue 3, FastAPI & LangGraph. AI Empowers Engineering.*
