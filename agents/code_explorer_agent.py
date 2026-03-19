"""
agents/code_explorer_agent.py
Fixed: now correctly reads issue_reader output from shared session memory.
"""

from llm.llm_client import ask_llm_json
from memory.session_store import session
from github.github_client import get_repo_contents

SYSTEM_PROMPT = """
You are an expert software engineer who specializes in navigating and understanding codebases.
Your job is to identify which files and areas of a codebase are most relevant to a GitHub issue.
Be specific and practical. Always respond with valid JSON only.
"""

def _fetch_repo_tree(owner: str, repo: str, path: str = "", depth: int = 0, max_depth: int = 2) -> list:
    if depth > max_depth:
        return []
    items = get_repo_contents(owner, repo, path)
    tree = []
    for item in items[:30]:
        if item.get("type") == "file":
            tree.append(item.get("path", ""))
        elif item.get("type") == "dir" and depth < max_depth:
            subtree = _fetch_repo_tree(owner, repo, item.get("path", ""), depth + 1, max_depth)
            tree.extend(subtree)
    return tree

def explore_codebase(plan: dict = None, repo_structure: list = None) -> dict:
    # Read from session memory — this is the fix
    issue_data = session.get("issue_reader")
    plan_data = session.get("planner")

    if not issue_data or not isinstance(issue_data, dict) or "error" in issue_data:
        print("[CodeExplorer] No valid issue data in memory. Run read_issue() first.")
        return {"error": "IssueReader output missing from session.",
                "suspected_areas": [], "files_to_check": [], "reasoning": []}

    repo = issue_data.get("repo", "")
    if not repo or "/" not in repo:
        print("[CodeExplorer] No repo info in session.")
        return {"error": "No repo in session.", "suspected_areas": [], "files_to_check": [], "reasoning": []}

    owner, repo_name = repo.split("/", 1)

    print(f"[CodeExplorer] Fetching real repo structure for {repo}...")
    file_tree = _fetch_repo_tree(owner, repo_name)

    if file_tree:
        file_tree_str = "\n".join(file_tree[:80])
        print(f"[CodeExplorer] Found {len(file_tree)} files.")
    else:
        file_tree_str = "Could not fetch repo structure — using issue context only."
        print("[CodeExplorer] Could not fetch repo tree. Using LLM only.")

    user_prompt = f"""
Based on this GitHub issue analysis, identify the most relevant files in the codebase.

Full context from previous agents:
{session.summary()}

Actual repo file structure ({repo}):
{file_tree_str}

Return a JSON object with these exact keys:
- "suspected_areas": list of 2-4 module or folder names likely involved (list of strings)
- "files_to_check": list of 3-6 specific file paths from the repo tree above (list of strings)
- "reasoning": list of short explanations for why each area is relevant (list of strings)
- "entry_points": list of function or class names to look for (list of strings)
- "search_keywords": list of keywords to search in the codebase (list of strings)
- "confidence": your confidence from 0.0 to 1.0 (float)
"""

    print("[CodeExplorer] Identifying relevant files with LLM...")
    result = ask_llm_json(SYSTEM_PROMPT, user_prompt)
    result["repo_files_scanned"] = len(file_tree)

    session.set("code_explorer", result)
    print(f"[CodeExplorer] Done. Files: {len(result.get('files_to_check', []))} | Confidence: {result.get('confidence')}")
    return result
