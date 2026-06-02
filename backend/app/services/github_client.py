# backend/app/services/github_client.py
import httpx
import re
from fastapi import HTTPException
from app.core.config import settings


class GithubClient:
    def __init__(self):
        # 基础请求头
        self.base_headers = {
            "X-GitHub-Api-Version": "2022-11-28"
        }
        if settings.GITHUB_TOKEN:
            self.base_headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    def parse_pr_url(self, url: str) -> dict:
        """
        从 PR 链接中提取 owner, repo 和 pull_number
        例如: https://github.com/vuejs/core/pull/1234
        """
        pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
        match = re.search(pattern, str(url))
        if not match:
            raise ValueError("无效的 GitHub PR 链接格式")

        return {
            "owner": match.group(1),
            "repo": match.group(2),
            "pull_number": match.group(3)
        }

    async def get_pr_diff(self, url: str) -> str:
        """
        异步获取 PR 的具体代码变更 (Diff 格式)
        """
        try:
            repo_info = self.parse_pr_url(url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # 构建 GitHub API URL
        api_url = f"https://api.github.com/repos/{repo_info['owner']}/{repo_info['repo']}/pulls/{repo_info['pull_number']}"

        # 请求 Diff 格式的关键 Header
        headers = self.base_headers.copy()
        headers["Accept"] = "application/vnd.github.v3.diff"

        async with httpx.AsyncClient() as client:
            response = await client.get(api_url, headers=headers, timeout=15.0)

            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="找不到该 PR，请检查链接或确保仓库是公开的/Token有效。")
            elif response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=f"GitHub API 请求失败: {response.text}")

            return response.text

    async def get_file_content(self, repo_name: str, file_path: str, branch: str = "main") -> str:
        """
        异步获取指定仓库中特定文件的源码 (供 AI Agent 主动检索上下文使用)
        :param repo_name: 格式如 "vuejs/core"
        :param file_path: 文件的相对路径, 如 "src/utils/index.ts"
        :param branch: 分支名, 默认 "main"
        """
        api_url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}?ref={branch}"

        # 请求 raw 格式的关键 Header，直接获取纯代码文本
        headers = self.base_headers.copy()
        headers["Accept"] = "application/vnd.github.v3.raw"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(api_url, headers=headers, timeout=10.0)

                if response.status_code == 200:
                    return response.text
                elif response.status_code == 404:
                    return f"Error: 文件 {file_path} 不存在于分支 {branch} 中。请检查路径。"
                else:
                    return f"Error: 无法获取文件内容，状态码 {response.status_code}"
            except Exception as e:
                return f"Error: 请求源码时发生网络异常: {str(e)}"


# 实例化一个单例供外部调用
github_client = GithubClient()