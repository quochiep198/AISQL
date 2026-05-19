# SQL Query Review & Optimization Assistant

Sourcebase MVP theo spec-pack: React/Vite frontend + FastAPI backend, uu tien deploy tren Vercel.

## Cau truc

```txt
query-reviewer/
|-- api/
|   `-- index.py
|-- app/
|   |-- main.py
|   |-- schemas.py
|   |-- services/
|   `-- utils/
|-- frontend/
|   `-- src/
|-- requirements.txt
|-- vercel.json
`-- .env.example
```

## Chay local backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```bash
curl http://localhost:8000/api/health
```

## Chay local frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend mac dinh goi `/api/review`. Khi chay Vite local, proxy trong `vite.config.ts` se chuyen API sang `http://localhost:8000`.

## AI review voi Gemini, Groq hoac Claude

Backend hien ho tro 3 provider bang API key:
- `gemini` qua SDK `google-genai`
- `groq` qua SDK `openai` voi endpoint OpenAI-compatible
- `claude` qua SDK `anthropic`

Can cau hinh `.env`:

### Gemini

```env
ENABLE_AI_REVIEW=true
AI_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
AI_TIMEOUT_SECONDS=20
```

### Groq

```env
ENABLE_AI_REVIEW=true
AI_PROVIDER=groq
GROQ_API_KEY=...
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.3-70b-versatile
AI_TIMEOUT_SECONDS=20
```

### Claude

```env
ENABLE_AI_REVIEW=true
AI_PROVIDER=claude
ANTHROPIC_API_KEY=...
CLAUDE_MODEL=claude-sonnet-4-20250514
AI_TIMEOUT_SECONDS=20
```

Neu khong bat AI review, he thong se fallback ve rule-based analyzer.

## Deploy Vercel

1. Push sourcebase len GitHub.
2. Import project vao Vercel.
3. Root Directory mac dinh la root repo.
4. Vercel doc `vercel.json`:
   - install: `cd frontend && npm install`
   - build: `cd frontend && npm run build`
   - output: `frontend/dist`
   - route `/api/*` ve `api/index.py`
   - route con lai fallback ve `frontend/dist/index.html`
5. Them environment variables neu can:
   - `ENABLE_AI_REVIEW=false` cho rule-based only
   - `AI_PROVIDER=gemini` hoac `AI_PROVIDER=groq` hoac `AI_PROVIDER=claude`
   - `GEMINI_API_KEY` neu dung Gemini
   - `GEMINI_MODEL` neu dung Gemini
   - `GROQ_API_KEY` neu dung Groq
   - `GROQ_BASE_URL=https://api.groq.com/openai/v1` neu dung Groq
   - `ANTHROPIC_API_KEY` neu dung Claude
   - `GROQ_MODEL` neu dung Groq
   - `CLAUDE_MODEL` neu dung Claude

`AI_MODEL` van duoc ho tro de tuong thich nguoc, nhung chi duoc dung khi phu hop voi provider dang chon. Neu `AI_PROVIDER=claude` ma `AI_MODEL=llama-3.3-70b-versatile`, backend se bo qua `AI_MODEL` va dung `CLAUDE_MODEL` hoac model mac dinh cua Claude.

## API

### POST `/api/review`

Request:

```json
{
  "query": "SELECT * FROM users WHERE email LIKE '%gmail.com'",
  "database_type": "mysql",
  "context": "users co khoang 2 trieu records",
  "optimization_goal": "speed"
}
```

Response gom:

- `detected_type`
- `score`
- `summary`
- `issues`
- `improvements`
- `optimized_query`
- `notes`

## Luu y bao mat

MVP khong ket noi database that, khong execute query va khong luu query mac dinh.
