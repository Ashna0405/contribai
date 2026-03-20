import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            github_login VARCHAR(100) UNIQUE NOT NULL,
            name VARCHAR(200),
            avatar_url TEXT,
            email VARCHAR(200),
            public_repos INTEGER DEFAULT 0,
            followers INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            last_login TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id SERIAL PRIMARY KEY,
            github_login VARCHAR(100) NOT NULL,
            repo VARCHAR(200) NOT NULL,
            issue_number INTEGER NOT NULL,
            pr_title TEXT,
            issue_type VARCHAR(100),
            confidence FLOAT DEFAULT 0,
            agent_scores JSONB DEFAULT '{}',
            full_output JSONB DEFAULT '{}',
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS badges (
            id SERIAL PRIMARY KEY,
            github_login VARCHAR(100) NOT NULL,
            badge_id VARCHAR(100) NOT NULL,
            earned_at TIMESTAMP DEFAULT NOW(),
            UNIQUE(github_login, badge_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            github_login VARCHAR(100) PRIMARY KEY,
            theme VARCHAR(20) DEFAULT 'dark',
            default_owner VARCHAR(100) DEFAULT '',
            default_repo VARCHAR(100) DEFAULT '',
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("[DB] Tables initialized.")

def upsert_user(user_data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (github_login, name, avatar_url, email, public_repos, followers, last_login)
        VALUES (%(login)s, %(name)s, %(avatar)s, %(email)s, %(public_repos)s, %(followers)s, NOW())
        ON CONFLICT (github_login) DO UPDATE SET
            name = EXCLUDED.name,
            avatar_url = EXCLUDED.avatar_url,
            email = EXCLUDED.email,
            public_repos = EXCLUDED.public_repos,
            followers = EXCLUDED.followers,
            last_login = NOW()
    """, user_data)
    conn.commit()
    cur.close()
    conn.close()

def save_analysis(github_login, repo, issue_number, result):
    conn = get_connection()
    cur = conn.cursor()
    pr_data = result.get("pr_helper", {})
    plan_data = result.get("planner", {})
    agent_scores = {
        "issue_reader": result.get("issue_reader", {}).get("confidence", 0),
        "planner": result.get("planner", {}).get("confidence", 0),
        "code_explorer": result.get("code_explorer", {}).get("confidence", 0),
        "solution": result.get("solution", {}).get("confidence", 0),
        "pr_helper": result.get("pr_helper", {}).get("confidence", 0),
    }
    cur.execute("""
        INSERT INTO analyses (github_login, repo, issue_number, pr_title, issue_type, confidence, agent_scores, full_output)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        github_login, repo, issue_number,
        pr_data.get("title", ""),
        plan_data.get("issue_type", ""),
        pr_data.get("confidence", 0),
        json.dumps(agent_scores),
        json.dumps(result)
    ))
    conn.commit()
    cur.close()
    conn.close()

def get_user_analyses(github_login):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT repo, issue_number as issue, pr_title, issue_type,
               confidence, agent_scores, created_at
        FROM analyses WHERE github_login = %s
        ORDER BY created_at DESC LIMIT 50
    """, (github_login,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

def get_user_stats(github_login):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as total,
               AVG(confidence) as avg_confidence,
               COUNT(DISTINCT repo) as unique_repos
        FROM analyses WHERE github_login = %s
    """, (github_login,))
    stats = dict(cur.fetchone())
    cur.close()
    conn.close()
    return stats

def check_and_award_badges(github_login):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) as total, AVG(confidence) as avg_conf,
               COUNT(DISTINCT repo) as repos
        FROM analyses WHERE github_login = %s
    """, (github_login,))
    stats = dict(cur.fetchone())
    total = stats["total"] or 0
    avg_conf = float(stats["avg_conf"] or 0)
    repos = stats["repos"] or 0
    badge_rules = [
        ("first_look", total >= 1),
        ("power_user", total >= 10),
        ("explorer", repos >= 5),
        ("deep_thinker", avg_conf >= 0.9),
        ("contributor", total >= 5),
    ]
    new_badges = []
    for badge_id, condition in badge_rules:
        if condition:
            try:
                cur.execute("""
                    INSERT INTO badges (github_login, badge_id)
                    VALUES (%s, %s) ON CONFLICT DO NOTHING
                """, (github_login, badge_id))
                if cur.rowcount > 0:
                    new_badges.append(badge_id)
            except Exception:
                pass
    conn.commit()
    cur.close()
    conn.close()
    return new_badges

def get_user_badges(github_login):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT badge_id, earned_at FROM badges WHERE github_login = %s ORDER BY earned_at", (github_login,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]

def get_settings(github_login):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM settings WHERE github_login = %s", (github_login,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else {"theme": "dark", "default_owner": "", "default_repo": ""}

def save_settings(github_login, settings):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO settings (github_login, theme, default_owner, default_repo)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (github_login) DO UPDATE SET
            theme = EXCLUDED.theme,
            default_owner = EXCLUDED.default_owner,
            default_repo = EXCLUDED.default_repo,
            updated_at = NOW()
    """, (github_login, settings.get("theme","dark"), settings.get("default_owner",""), settings.get("default_repo","")))
    conn.commit()
    cur.close()
    conn.close()
