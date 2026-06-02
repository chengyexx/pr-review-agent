# backend/app/agents/nodes/scout.py
from unidiff import PatchSet
from app.agents.state import PRReviewState
from app.core.log_util import safe_print

# Files with these extensions are considered "doc-only" (skip deep code review)
DOC_ONLY_EXTENSIONS = {".md", ".txt", ".rst", ".adoc"}


def scout_node(state: PRReviewState) -> dict:
    """
    Scout node: analyze diff complexity, decide whether this PR is trivial.
    Uses per-file PatchSet analysis instead of whole-diff string matching
    to avoid false "trivial" classification for mixed-content PRs.
    """
    safe_print("[Agent->Scout] Analyzing PR changes and complexity...")
    diff = state.get("diff_content", "")

    if len(diff.strip()) == 0:
        return {"is_trivial": True, "skip_reason": "Empty commit or no effective code changes."}

    # Parse diff per-file: only skip if ALL changed files are doc-only
    try:
        patch_set = PatchSet(diff)
        code_files_found = False
        for patched_file in patch_set:
            if patched_file.is_removed_file:
                continue
            ext = ""
            if "." in patched_file.path:
                _, ext = patched_file.path.rsplit(".", 1)
                ext = "." + ext
            if ext not in DOC_ONLY_EXTENSIONS:
                code_files_found = True
                break

        if not code_files_found:
            return {"is_trivial": True, "skip_reason": "Doc-only changes, no deep review needed."}
    except Exception as e:
        safe_print(f"[Agent->Scout] WARNING: diff parse failed, allowing deep review: {e}")

    safe_print("[Agent->Scout] Core code changes detected, routing to evaluate node.")
    return {"is_trivial": False, "skip_reason": ""}
