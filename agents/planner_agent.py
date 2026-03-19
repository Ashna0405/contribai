"""
agents/planner_agent.py
Upgraded from your original plan_issue() function.
Before: simple if/else on labels list — only detected "bug" keyword.
Now: LLM reasons about the issue and creates a real action plan from memory.
"""

from llm.llm_client import ask_llm_json
from memory.session_store import session

SYSTEM_PROMPT = """
You are a senior software engineer and open source maintainer.
Your job is to create a clear, actionable plan for how a developer should approach a GitHub issue.
Think step by step. Be specific. Always respond with valid JSON only.
"""


def plan_issue(parsed_issue: dict = None) -> dict:
    """
    Upgraded from your original version.
    Before: took parsed_issue as arg, used if/else on labels.
    Now: reads from shared memory, uses LLM for real reasoning.
    The parsed_issue arg is kept for backward compatibility but ignored —
    we read from session instead so all agent context is available.
    """
    issue_data = session.get("issue_reader")

    if not issue_data or "error" in issue_data:
        print("[Planner] No valid issue data in memory. Run read_issue() first.")
        return {"error": "IssueReader output missing from session."}

    user_prompt = f"""
Based on this analyzed GitHub issue, create a detailed action plan for a developer.

Issue Analysis from previous agent:
{session.summary()}

Return a JSON object with these exact keys:
- "issue_type": one of "bug_fix", "feature_implementation", "refactor", "docs_update", "investigation" (string)
- "complexity": one of "simple", "moderate", "complex" (string)
- "possible_causes": list of 2-4 possible root causes for this issue (list of strings)
- "approach": short paragraph describing the overall approach (string)
- "next_steps": ordered list of 4-6 concrete action steps (list of strings)
- "skills_needed": list of technologies or skills needed (list of strings)
- "estimated_time": rough estimate like "2-4 hours" or "1-2 days" (string)
- "confidence": your confidence from 0.0 to 1.0 in this plan (float)
"""

    print("[Planner] Creating action plan with LLM...")
    result = ask_llm_json(SYSTEM_PROMPT, user_prompt)

    session.set("planner", result)
    print(f"[Planner] Done. Type: {result.get('issue_type')} | Complexity: {result.get('complexity')} | Confidence: {result.get('confidence')}")
    return result