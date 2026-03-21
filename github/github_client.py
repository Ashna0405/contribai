"""
github/github_client.py
Upgraded from your original version.
Added: retries, rate limit handling, 404/401 errors, repo file fetching.
"""

import os
import time
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
BASE_URL = "https://api.github.com"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


def get_issue(owner: str, repo: str, issue_number: int) -> dict:
    """
    Fetch a GitHub issue — upgraded from your original with error handling.
    Returns structured data or a safe error dict (never crashes).
    """
    url = f"{BASE_URL}/repos/{owner}/{repo}/issues/{issue_number}"

    for attempt in range(3):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    "id": data.get("number"),
                    "title": data.get("title", ""),
                    "body": data.get("body", "") or "No description provided.",
                    "labels": [l["name"] for l in data.get("labels", [])],
                    "state": data.get("state", "open"),
                    "author": data.get("user", {}).get("login", "unknown"),
                    "comments_count": data.get("comments", 0),
                    "url": data.get("html_url", ""),
                    "repo": f"{owner}/{repo}",
                }

            elif response.status_code == 404:
                return {"error": f"Issue #{issue_number} does not exist in {owner}/{repo}. Please check the issue number and try again."}

            elif response.status_code == 401:
                return {"error": "Invalid GITHUB_TOKEN. Check your .env file."}

            elif response.status_code == 403:
                # Rate limit — wait and retry
                reset_time = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait = max(reset_time - int(time.time()), 5)
                print(f"[GitHub] Rate limit hit. Waiting {wait}s...")
                time.sleep(wait)

            else:
                return {"error": f"GitHub API returned status {response.status_code}"}

        except requests.exceptions.Timeout:
            print(f"[GitHub] Timeout on attempt {attempt+1}. Retrying...")
            time.sleep(2 ** attempt)

        except requests.exceptions.ConnectionError:
            return {"error": "No internet connection or GitHub is unreachable."}

    return {"error": "GitHub API failed after 3 retries."}


def get_repo_contents(owner: str, repo: str, path: str = "") -> list:
    """Fetch file/folder listing from a GitHub repo for Code Explorer."""
    url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


def get_file_content(owner: str, repo: str, file_path: str) -> str:
    """Fetch and decode the actual content of a file from GitHub."""
    url = f"{BASE_URL}/repos/{owner}/{repo}/contents/{file_path}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        return ""
    except Exception:
        return ""