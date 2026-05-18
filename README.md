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

## AI review voi Groq

Backend su dung SDK `openai` theo giao thuc OpenAI-compatible cua Groq.

Can cau hinh:

```env
ENABLE_AI_REVIEW=true
GROQ_API_KEY=...
GROQ_BASE_URL=https://api.groq.com/openai/v1
AI_MODEL=llama-3.3-70b-versatile
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
   - API rewrite ve `api/index.py`
5. Them environment variables neu can:
   - `ENABLE_AI_REVIEW=false` cho rule-based only
   - `GROQ_API_KEY` neu bat AI review
   - `GROQ_BASE_URL=https://api.groq.com/openai/v1`
   - `AI_MODEL`

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
