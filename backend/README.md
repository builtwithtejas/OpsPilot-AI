# OpsPilot AI — Backend

AI-Powered DevOps Incident Intelligence Platform.

## Setup

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # then fill in your keys
```

## Running

```bash
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`.

## Authentication

All endpoints (except `/` and `/health`) require an `X-API-Key` header:

```
X-API-Key: your-api-key-here
```

Set `API_KEY` in your `.env` file.

## Environment variables

| Variable | Description | Default |
|---|---|---|
| `API_KEY` | Secret key for API auth | `change-this-secret-api-key` |
| `GROQ_API_KEY` | Groq LLM API key | — |
| `GITHUB_TOKEN` | GitHub personal access token | — |
| `GITHUB_REPO` | GitHub repo (`owner/name`) | — |
| `DATABASE_URL` | SQLAlchemy DB URL | `sqlite:///./opspilot.db` |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000` |
| `MAX_UPLOAD_SIZE_MB` | Max log upload size in MB | `10` |

## Running tests

```bash
pytest tests/ -v
```
