# 代码 RAG 检索引擎 — 预留扩展接口
#
# 未来将使用 FAISS / Chroma 向量数据库实现：
# 1. 索引项目全量代码库
# 2. PR 审查时检索跨文件依赖上下文
# 3. 注入团队 CONTRIBUTING.md 规范实现定制化评审
#
# 当前阶段使用 evaluate.py 内置的 GitHub API 文件拉取作为上下文获取方式。
