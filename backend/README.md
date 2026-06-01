## OpsPilot AI 🤖

> Autonomous DevSecOps agent — from pipeline failure to fix MR in 28 seconds.

## Built With
| Service | Usage |
|---|---|
| GitLab Duo Agent Platform | Custom agent (ID: 1009889), MCP integration |
| Google Gemini 2.5 Flash | Log analysis, risk forecasting, auto-fix generation |
| Google Cloud Agent Builder | Agent orchestration architecture |
| GitLab CI/CD | Pipeline monitoring via webhook |
| FastAPI + SQLite | Backend API |
| Next.js 14 | Real-time dashboard |

## The 7-Step Agent Loop
1. **Detect** — GitLab webhook fires on pipeline failure
2. **Gather** — Fetch job logs from failed pipeline  
3. **Analyse** — Gemini 2.5 Flash analyses root cause
4. **Record** — Persist incident with severity + confidence
5. **Act** — Auto-create GitLab issue + MR comment
6. **Notify** — Slack webhook + SendGrid email
7. **Duo** — Notify GitLab Duo Agent Platform

## Setup
### Environment Variables
| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio API key |
| `GITLAB_TOKEN` | GitLab Personal Access Token (api scope) |
| `GITLAB_BASE_URL` | https://gitlab.com |
| `GITLAB_AGENT_ID` | 1009889 |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |
| `SENDGRID_API_KEY` | SendGrid API key |
| `API_KEY` | OpsPilot backend API key |
| `DATABASE_URL` | SQLite or PostgreSQL connection string |

### Run locally
\`\`\`bash
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload
\`\`\`

### GitLab Webhook Setup
URL: `https://your-render-url/webhooks/gitlab`  
Trigger: Pipeline events  
Secret: value of `GITLAB_WEBHOOK_SECRET`