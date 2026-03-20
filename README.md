# ⚡ ContribAI

> A multi-agent AI system that analyzes GitHub issues and guides developers through open source contributions.

🌐 **Live Demo:** [web-production-11ea7.up.railway.app](https://web-production-11ea7.up.railway.app)

---

## 🧠 What is ContribAI?

ContribAI is a production-grade agentic AI system built for developers who want to contribute to open source but don't know where to start. It takes any GitHub issue and runs it through a pipeline of 5 specialized AI agents — each with a single responsibility — to produce a complete contribution guide and PR draft.

---

## 🏗️ System Architecture
```
GitHub Issue URL
      ↓
Issue Reader Agent    →  Understands the issue deeply
      ↓
Planner Agent         →  Creates an action plan
      ↓
Code Explorer Agent   →  Scans real repo files on GitHub
      ↓
Solution Agent        →  Proposes a concrete fix
      ↓
PR Helper Agent       →  Drafts a professional PR description
```

Each agent has a **single responsibility**, reads from **shared session memory**, and scores its own output with a **confidence score**.

---

## ✨ Features

- 🤖 **5 AI Agents** powered by Groq (Llama 3.3 70B)
- 🔍 **Real codebase parsing** — scans actual GitHub repo file structure
- 🧠 **Shared session memory** — agents pass context to each other
- 📊 **Confidence scoring** — every agent rates its own output
- 🔐 **GitHub OAuth login** — sign in with your GitHub account
- 📈 **Evaluation dashboard** — charts and history of all analyses
- 👤 **Profile page** — GitHub stats, badges, activity timeline
- 🏆 **Achievement badges** — earned through usage milestones
- ⚙️ **Settings** — theme toggle, default repo preferences
- 🗄️ **PostgreSQL database** — persistent storage via Railway
- 🚀 **Deployed** — live on Railway with auto-deploy from GitHub

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| LLM | Groq API (Llama 3.3 70B) |
| Database | PostgreSQL (Railway) |
| Auth | GitHub OAuth 2.0 |
| GitHub API | REST API v3 |
| Frontend | HTML, CSS, Vanilla JS |
| Deployment | Railway |

---

## 📁 Project Structure
```
contribai/
│
├── agents/
│   ├── issue_reader_agent.py    # Agent 1 — reads & understands issue
│   ├── planner_agent.py         # Agent 2 — creates action plan
│   ├── code_explorer_agent.py   # Agent 3 — scans real repo files
│   ├── solution_agent.py        # Agent 4 — proposes solution
│   └── pr_helper_agent.py       # Agent 5 — drafts PR description
│
├── github/
│   └── github_client.py         # GitHub REST API client
│
├── memory/
│   └── session_store.py         # Shared memory between agents
│
├── llm/
│   └── llm_client.py            # Groq LLM wrapper
│
├── templates/
│   ├── login.html               # Login page
│   ├── index.html               # Analyze page
│   ├── dashboard.html           # Dashboard page
│   ├── profile.html             # Profile page
│   └── settings.html            # Settings page
│
├── database.py                  # PostgreSQL operations
├── app.py                       # Flask app + routes
├── main.py                      # CLI runner
└── requirements.txt
```

---

## 🚀 Running Locally

**1. Clone the repo:**
```bash
git clone https://github.com/Ashna0405/contribai.git
cd contribai
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Create `.env` file:**
```env
GITHUB_TOKEN=your_github_token
GROQ_API_KEY=your_groq_api_key
GITHUB_CLIENT_ID=your_oauth_client_id
GITHUB_CLIENT_SECRET=your_oauth_client_secret
SECRET_KEY=your_secret_key
DATABASE_URL=your_postgresql_url
```

**4. Run:**
```bash
python app.py
```

**5. Open:** `http://127.0.0.1:8080`

---

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `GITHUB_TOKEN` | GitHub Personal Access Token |
| `GROQ_API_KEY` | Groq API key (free at console.groq.com) |
| `GITHUB_CLIENT_ID` | GitHub OAuth App Client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Client Secret |
| `SECRET_KEY` | Flask session secret key |
| `DATABASE_URL` | PostgreSQL connection URL |

---

## 🏆 Achievement Badges

| Badge | How to Earn |
|---|---|
| 🔍 First Look | Analyze your first issue |
| 🤝 Contributor | Analyze 5 issues |
| 🚀 Power User | Analyze 10 issues |
| 🌟 Explorer | Analyze 5 different repos |
| 🧠 Deep Thinker | Achieve avg confidence above 0.9 |

---

## ⚠️ Limitations

- No real code execution or automatic fixes
- Code exploration is based on file tree heuristics
- Depends on issue quality for best results
- LLM responses may vary

---

## 🔭 Future Scope

- [ ] Feedback loop between agents (reviewer agent)
- [ ] Few-shot prompts for better output quality
- [ ] Vector memory (RAG) with ChromaDB
- [ ] Real code snippet suggestions
- [ ] GitHub PR auto-creation
- [ ] Multi-language support

---

## 👩‍💻 Built By

**Ashna** — 3rd Year AI & Data Science Student

---

## 📄 License

MIT License — feel free to use and modify!
