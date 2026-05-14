# Testing Checklist Chatbot

A bachelor's thesis project. An LLM-powered chatbot that conversationally collects information about a software project and generates a prioritized testing checklist (HIGH / MEDIUM / LOW) exportable to Excel. Supports web, mobile, desktop, and API application types, and dynamically generates specialist rules for novel types.

Developed and tested on a MacBook Pro M4 Pro with 24 GB RAM. Local Ollama models (`qwen2.5:latest`, `gpt-oss:20b`) require comparable hardware.

---

## Tech stack

**Backend** — Python 3.12+, FastAPI, LangChain + Ollama, Supabase, `uv`

**Frontend** — React 19, Vite 8, Tailwind CSS 4, Supabase JS

---

## Prerequisites

- Python 3.12+
- Node.js 20+
- [`uv`](https://docs.astral.sh/uv/) package manager
- [Ollama](https://ollama.com) running locally with the required models pulled:
  ```bash
  ollama pull qwen2.5:latest
  ollama pull gpt-oss:20b
  ```
- A [Supabase](https://supabase.com) project (URL + anon/service key)

---

## Backend setup

```bash
cd backend
uv sync
```

Create `backend/.env`:

```env
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_KEY=<your-service-role-or-anon-key>
LOG_LEVEL=INFO          # optional, defaults to DEBUG
```

Start the server (port 8000):

```bash
uv run uvicorn main:app --reload
```

---

## Frontend setup

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://<your-project>.supabase.co
VITE_SUPABASE_ANON_KEY=<your-anon-key>
```

Start the dev server (port 5173 — required, hardcoded in backend CORS):

```bash
npm run dev
```

---

## Tests & linting

```bash
# from backend/
uv run pytest
uv run ruff check
```
