"""
agents/issue_reader_agent.py
Upgraded from your original read_issue() function.
Before: just extracted 3 fields from raw JSON.
Now: LLM reads and understands the issue deeply, saves to shared memory.
"""

from llm.llm_client import ask_llm_json
from memory.session_store import session

SYSTEM_PROMPT = """
You are an expert open source contributor who specializes in understanding GitHub issues.
Your job is to read a raw GitHub issue and extract structured, useful information from it.
Always respond with valid JSON only.
"""


def read_issue(issue_data: dict) -> dict:
    """
    Upgraded from your original version.
    Before: returned only title, description, labels.
    Now: LLM extracts deep understanding and saves to shared session memory.
    """
    if "error" in issue_data:
        print(f"[IssueReader] Error in issue data: {issue_data['error']}")
        return issue_data

    user_prompt = f"""
Analyze this GitHub issue and return a JSON object with these exact keys:
- "title": the issue title (string)
- "description": a clear 2-3 sentence summary of the problem (string)
- "issue_category": one of "bug", "feature_request", "documentation", "question", "performance", "security" (string)
- "severity": one of "critical", "high", "medium", "low" (string)
- "labels": list of labels from the issue (list of strings)
- "key_terms": important technical keywords from the issue (list of strings)
- "beginner_friendly": true if suitable for a beginner contributor, false otherwise (boolean)
- "confidence": your confidence from 0.0 to 1.0 in this analysis (float)

GitHub Issue:
Title: {issue_data.get('title')}
Body: {issue_data.get('body')}
Labels: {issue_data.get('labels')}
Author: {issue_data.get('author')}
Comments: {issue_data.get('comments_count')}
"""

    print("[IssueReader] Analyzing issue with LLM...")
    result = ask_llm_json(SYSTEM_PROMPT, user_prompt)

    # Preserve original metadata
    result["url"] = issue_data.get("url", "")
    result["repo"] = issue_data.get("repo", "")
    result["issue_number"] = issue_data.get("id", "")

    # Save to shared memory so other agents can read it
    session.set("issue_reader", result)
    print(f"[IssueReader] Done. Category: {result.get('issue_category')} | Severity: {result.get('severity')} | Confidence: {result.get('confidence')}")
    return result