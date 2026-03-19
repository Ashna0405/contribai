"""
agents/pr_helper_agent.py
Upgraded from your original draft_pr() function.
Before: template strings with hardcoded "streaming" reviewer note regardless of issue.
Now: LLM writes a real, contextual PR description from full pipeline memory.
"""

from llm.llm_client import ask_llm_json
from memory.session_store import session

SYSTEM_PROMPT = """
You are an experienced open source contributor who writes excellent Pull Request descriptions.
Your PRs are clear, professional, and give reviewers everything they need.
Always respond with valid JSON only.
"""


def draft_pr(issue: dict = None, plan: dict = None, exploration: dict = None, solution: dict = None) -> dict:
    """
    Upgraded from your original version.
    Before: took 4 args, used template strings, hardcoded reviewer notes about streaming.
    Now: reads full session memory, LLM writes a proper contextual PR.
    Args kept for backward compatibility with your main.py call signature.
    """
    if not session.get("solution"):
        print("[PRHelper] Missing solution data in session. Run previous agents first.")
        return {"error": "Run all previous agents first.",
                "title": "", "summary": "", "changes": [], "tests": [], "notes_for_reviewer": []}

    user_prompt = f"""
Using the full pipeline analysis, draft a complete professional Pull Request description.

Full pipeline context:
{session.summary()}

Return a JSON object with these exact keys:
- "title": PR title in conventional commits format e.g. "fix: ..." or "feat: ..." (string)
- "summary": 2-3 sentence summary of what this PR does and why (string)
- "problem_statement": what problem this PR solves (string)
- "solution_description": how the PR solves it (string)
- "changes": list of specific changes made in this PR (list of strings)
- "tests": list of tests added or modified (list of strings)
- "screenshots_needed": true if UI changes need screenshots, false otherwise (boolean)
- "breaking_changes": true if this breaks existing functionality, false otherwise (boolean)
- "notes_for_reviewer": specific things the reviewer should pay attention to (string)
- "checklist": PR checklist items like "Tests pass", "Docs updated" (list of strings)
- "confidence": your confidence from 0.0 to 1.0 in this PR draft (float)
"""

    print("[PRHelper] Drafting PR with LLM...")
    result = ask_llm_json(SYSTEM_PROMPT, user_prompt)

    session.set("pr_helper", result)
    print(f"[PRHelper] Done. Title: {result.get('title')} | Confidence: {result.get('confidence')}")
    return result