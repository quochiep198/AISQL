# Gói đặc tả — [1] (SQL Query Review & Optimization Assistant)

> Tạo: 2026-05-18 · Giai đoạn: MVP
> **Nguồn tham chiếu duy nhất cho thay đổi này.**  
> Không triển khai bất kỳ nội dung nào không được viết ở đây. Các điểm chưa rõ → Open Issues.

---

## 1. Bối cảnh / Mục đích

Xây dựng website cho phép người dùng nhập câu truy vấn SQL/NoSQL, hệ thống sẽ phân tích và trả về nhận xét, rủi ro hiệu suất, gợi ý tối ưu và phiên bản truy vấn cải tiến nếu có thể.

## 2. Phạm vi

### Trong phạm vi

- Hỗ trợ review truy vấn dạng text cho MySQL.
- Hỗ trợ review truy vấn dạng text cho PostgreSQL.
- Hỗ trợ SQL Server / Oracle ở mức generic SQL.
- Hỗ trợ MongoDB query dạng JSON hoặc aggregation pipeline.
- Hỗ trợ NoSQL khác ở mức nhận diện và góp ý cơ bản.
- Backend dùng Python, FastAPI, Pydantic, Uvicorn cho local development.
- Có thể deploy backend trên Vercel Python Runtime / Serverless Functions.
- Frontend dùng Vite, React, TypeScript, Tailwind CSS hoặc CSS module.
- Kết hợp rule-based checks + LLM prompt review.
- Rule-based để phát hiện lỗi phổ biến.
- LLM để giải thích và đề xuất tối ưu dễ hiểu.
- Sử dụng GROQ như là AI để review code

### Ngoài phạm vi

- MVP chưa thực hiện kết nối trực tiếp database thật.
- Không cho phép upload file.
- Không chạy query.
- Không lưu query nhạy cảm mặc định.
- Không expose API key frontend.

## 3. Thuật ngữ

| #   | Thuật ngữ | Định nghĩa |
| --- | --------- | ---------- |
| 1   | MVP | Phiên bản sản phẩm tối thiểu trong phạm vi tài liệu này. |
| 2   | Rule-based analyzer | Cơ chế phân tích dựa trên rule cơ bản để phát hiện lỗi phổ biến. |
| 3   | LLM API | Hướng dùng AI để review nâng cao, giải thích và đề xuất tối ưu dễ hiểu. |
| 4   | `database_type` | Field optional nhận `mysql` / `postgres` / `mongodb` / `auto` hoặc enum API `auto | mysql | postgres | mongodb | generic_sql`. |
| 5   | `optimization_goal` | Field optional nhận `speed` / `readability` / `cost` / `index` / `general`. |
| 6   | `/api/review` | API endpoint dùng để review query. |
| 7   | `/api/health` | API endpoint kiểm tra trạng thái backend. |

## 4. Hiện trạng / Trạng thái mục tiêu

| #   | Khía cạnh | Hiện trạng | Trạng thái mục tiêu |
| --- | --------- | ---------- | ------------------- |
| 1   | Review truy vấn SQL/NoSQL | Chưa có | Người dùng nhập truy vấn SQL/NoSQL dạng text và nhận review gồm tổng quan, vấn đề phát hiện, gợi ý tối ưu, query đề xuất và mức độ rủi ro. |
| 2   | Kết nối database thật | MVP chưa thực hiện kết nối trực tiếp database thật. | Không execute query; không kết nối DB thật trong MVP. |
| 3   | AI review | MVP có thể dùng rule-based analyzer cơ bản hoặc LLM API để review nâng cao. | Khuyến nghị kết hợp rule-based checks + LLM prompt review; có thể bật/tắt AI review bằng env. |
| 4   | Deployment | Chưa | Chạy local được và deploy Vercel được. |

## 5. Chi tiết đặc tả

### 5.1 Kiến trúc tổng quan

```txt
User
  |
  v
Vite Frontend
  |
  | POST /api/review
  v
FastAPI Backend
  |
  | validate input
  | detect query type
  | run rule-based checks
  | optional AI review
  v
Review Result JSON
  |
  v
Frontend displays:
- Tổng quan
- Vấn đề phát hiện
- Gợi ý tối ưu
- Query đề xuất
- Mức độ rủi ro
```

### 5.2 Cấu trúc thư mục đề xuất

```txt
query-reviewer/
├── api/
│   └── index.py
├── app/
│   ├── main.py
│   ├── schemas.py
│   ├── services/
│   │   ├── detector.py
│   │   ├── rule_analyzer.py
│   │   ├── ai_reviewer.py
│   │   └── prompt_builder.py
│   └── utils/
│       └── sanitizer.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── QueryInput.tsx
│   │   │   ├── ReviewResult.tsx
│   │   │   └── ScoreBadge.tsx
│   │   └── api/
│   │       └── review.ts
│   ├── package.json
│   └── vite.config.ts
├── requirements.txt
├── vercel.json
└── README.md
```

### 5.3 Input

Người dùng nhập:

| Field | Type | Required | Description |
|---|---:|---:|---|
| query | string | yes | Câu truy vấn cần review |
| database_type | string | no | mysql / postgres / mongodb / auto |
| context | string | no | Mô tả bảng, index, số lượng dữ liệu, mục tiêu truy vấn |
| optimization_goal | string | no | speed / readability / cost / index / general |

Ví dụ:

```json
{
  "query": "SELECT * FROM users WHERE email LIKE '%gmail.com'",
  "database_type": "mysql",
  "context": "users có khoảng 2 triệu records",
  "optimization_goal": "speed"
}
```

### 5.4 Output

API trả về:

```json
{
  "detected_type": "mysql",
  "score": 62,
  "summary": "Query có thể chạy được nhưng có rủi ro hiệu suất do SELECT * và LIKE wildcard đầu chuỗi.",
  "issues": [
    {
      "severity": "high",
      "title": "LIKE với wildcard ở đầu chuỗi",
      "description": "Điều kiện LIKE '%gmail.com' thường không tận dụng được index thông thường.",
      "suggestion": "Cân nhắc tách domain email thành cột riêng và đánh index."
    }
  ],
  "improvements": [
    "Chỉ select các cột cần thiết thay vì SELECT *.",
    "Tạo index phù hợp cho cột thường dùng trong WHERE/JOIN/ORDER BY.",
    "Dùng EXPLAIN để kiểm tra execution plan."
  ],
  "optimized_query": "SELECT id, email, name FROM users WHERE email_domain = 'gmail.com';",
  "notes": [
    "Query tối ưu phụ thuộc schema thực tế.",
    "Cần kiểm tra bằng EXPLAIN ANALYZE trên database thật."
  ]
}
```

### 5.5 Rule-based checks MVP

#### SQL generic

Hệ thống cần phát hiện:

- `SELECT *`
- thiếu `WHERE` trong `UPDATE` / `DELETE`
- `LIKE '%keyword'`
- function trên indexed column
- `ORDER BY RAND()`
- `LIMIT` không có `ORDER BY`
- subquery có thể thay bằng JOIN
- `OR` nhiều điều kiện có thể ảnh hưởng index
- `OFFSET` lớn
- join thiếu điều kiện rõ ràng
- query quá dài hoặc nested quá sâu

#### PostgreSQL

- Gợi ý `EXPLAIN ANALYZE`
- Cảnh báo `ILIKE '%keyword%'`
- Gợi ý partial index
- Gợi ý JSONB index nếu query JSONB

#### MySQL

- Gợi ý `EXPLAIN`
- Cảnh báo `LIKE '%keyword%'`
- Cảnh báo implicit type conversion
- Gợi ý composite index theo thứ tự WHERE + ORDER BY

#### MongoDB / NoSQL

- Query không có filter
- Regex không anchored
- Aggregation pipeline thiếu `$match` sớm
- `$lookup` nặng
- thiếu index cho field filter/sort
- projection thiếu rõ ràng

### 5.6 API Specification

#### POST `/api/review`

##### Request

```json
{
  "query": "string",
  "database_type": "auto | mysql | postgres | mongodb | generic_sql",
  "context": "string",
  "optimization_goal": "general | speed | readability | index | cost"
}
```

##### Response 200

```json
{
  "detected_type": "string",
  "score": 0,
  "summary": "string",
  "issues": [
    {
      "severity": "low | medium | high | critical",
      "title": "string",
      "description": "string",
      "suggestion": "string"
    }
  ],
  "improvements": ["string"],
  "optimized_query": "string | null",
  "notes": ["string"]
}
```

##### Error 400

```json
{
  "detail": "Query is required"
}
```

### 5.7 Frontend MVP

#### Màn hình chính

Gồm:

1. Textarea nhập query
2. Dropdown chọn database type
3. Textarea nhập context optional
4. Button `Review Query`
5. Loading state
6. Khu vực hiển thị kết quả

#### UI kết quả

Hiển thị:

- Score badge
- Summary
- Issues theo severity
- Recommended improvements
- Optimized query block
- Notes / warnings

### 5.8 Prompt AI đề xuất

```txt
You are a senior database performance engineer.

Review the following query:

Database type:
{database_type}

Query:
{query}

Context:
{context}

Optimization goal:
{optimization_goal}

Return JSON only with:
- detected_type
- score from 0 to 100
- summary
- issues: severity, title, description, suggestion
- improvements
- optimized_query
- notes

Rules:
- Do not invent schema details.
- If schema/index information is missing, clearly mention assumptions.
- Prefer safe suggestions.
- Do not execute the query.
```

### 5.9 Vercel deployment design

#### Backend

FastAPI app expose biến `app`.

`api/index.py`:

```python
from app.main import app
```

`app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SQL Query Review API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

#### vercel.json

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "/api/index.py"
    }
  ]
}
```

#### requirements.txt

```txt
fastapi
pydantic
uvicorn
python-dotenv
openai
```

### 5.10 Environment Variables

```txt
OPENAI_API_KEY=
AI_MODEL=
ENABLE_AI_REVIEW=true
MAX_QUERY_LENGTH=10000
```

### 5.11 Validation

#### Input validation

- query không được rỗng
- query tối đa 10,000 ký tự
- database_type chỉ nhận enum hợp lệ
- không execute query
- sanitize output trước khi render

#### Security

MVP không kết nối DB thật.

Không cho phép:

- upload file
- chạy query
- lưu query nhạy cảm mặc định
- expose API key frontend

### 5.12 Roadmap sau MVP

#### Phase 2

- Lưu lịch sử review
- User login
- Export markdown/PDF
- Syntax highlighting
- Query formatter
- So sánh query gốc và query tối ưu

#### Phase 3

- Kết nối database read-only
- Upload EXPLAIN plan
- Phân tích execution plan
- Gợi ý index dựa trên schema thật
- Team workspace

#### Phase 4

- CI bot review SQL trong pull request
- GitHub integration
- Slack notification
- Database cost estimation

## 6. Yêu cầu phi chức năng

| #   | Danh mục          | Yêu cầu |
| --- | ----------------- | ------- |
| 1   | Hiệu năng         | Giới hạn input theo `MAX_QUERY_LENGTH=10000`; xử lý rủi ro serverless timeout bằng giới hạn input và timeout AI call. |
| 2   | Bảo mật           | Không kết nối DB thật; không execute query; không cho phép upload file; không lưu query nhạy cảm mặc định; không expose API key frontend; sanitize output trước khi render. |
| 3   | Tính sẵn sàng     | Có endpoint `/api/health`; chạy local được; deploy Vercel được. |
| 4   | Khả năng quan sát | Phải chi tiết và trực quan |

## 7. Tiêu chí chấp nhận

<!-- Mỗi AC phải là một phát biểu có thể kiểm thử được. -->

| #   | ID                | Mô tả | Loại kiểm thử |
| --- | ----------------- | ----- | ------------- |
| 1   | AC-query-review-1/v1 | Backend có endpoint `/api/health`. | IT |
| 2   | AC-query-review-2/v1 | Backend có endpoint `/api/review`. | IT |
| 3   | AC-query-review-3/v1 | Backend validate input đúng. | UT/IT |
| 4   | AC-query-review-4/v1 | Backend detect được SQL / MongoDB cơ bản. | UT/IT |
| 5   | AC-query-review-5/v1 | Backend trả về JSON theo format thống nhất. | IT |
| 6   | AC-query-review-6/v1 | Backend có ít nhất 10 rule review cơ bản. | UT |
| 7   | AC-query-review-7/v1 | Có thể bật/tắt AI review bằng env. | UT/IT |
| 8   | AC-query-review-8/v1 | Người dùng nhập query và submit được. | E2E |
| 9   | AC-query-review-9/v1 | Frontend hiển thị loading/error/success state. | E2E |
| 10   | AC-query-review-10/v1 | Frontend hiển thị score, issues, improvements, optimized query. | E2E |
| 11   | AC-query-review-11/v1 | UI responsive desktop/mobile cơ bản. | E2E |
| 12   | AC-query-review-12/v1 | Chạy local được. | BB |
| 13   | AC-query-review-13/v1 | Deploy Vercel được. | BB |
| 14   | AC-query-review-14/v1 | Không expose secret ra frontend. | BB |
| 15   | AC-query-review-15/v1 | MVP hoàn thành khi deploy được lên Vercel, người dùng nhập query và nhận review, kết quả có score/issues/improvements, có optimized query nếu đủ thông tin, có cảnh báo khi thiếu schema/index/context, không execute query, và có README hướng dẫn local và deploy. | E2E/BB |

## 8. Ví dụ

### Các luồng bình thường

1. Người dùng nhập query, chọn database type, nhập context optional, chọn optimization goal optional và bấm `Review Query`; frontend gọi `POST /api/review`; backend validate input, detect query type, chạy rule-based checks, optional AI review và trả về Review Result JSON.
2. Frontend hiển thị kết quả gồm Score badge, Summary, Issues theo severity, Recommended improvements, Optimized query block và Notes / warnings.

### Các luồng lỗi

1. Khi `query` rỗng, API trả về Error 400 với body:
```json
{
  "detail": "Query is required"
}
```
2. Khi input không hợp lệ, hệ thống validate theo các rule: query tối đa 10,000 ký tự và database_type chỉ nhận enum hợp lệ.

### Các trường hợp biên

1. Query có `LIMIT` không có `ORDER BY`.
2. Query có `OFFSET` lớn.
3. Query quá dài hoặc nested quá sâu.
4. MongoDB / NoSQL query không có filter.
5. Regex không anchored.
6. Aggregation pipeline thiếu `$match` sớm.
7. Schema/index information bị thiếu trong AI review thì AI phải clearly mention assumptions.

## 9. Wireframe ASCII (Tùy chọn)

<!-- Chỉ bao gồm khi thay đổi này thêm mới hoặc cập nhật UI/màn hình. Bỏ qua phần này nếu chỉ làm backend. -->

### Tên màn hình / luồng
Tham chiếu thiết kế tại thư mục raw/code.html(ở cùng thư mục)

### Ghi chú

- Các trạng thái chính: loading / error / success state.
- Thông điệp xác thực / lỗi: `Query is required`.
- Lưu ý về responsive hoặc mobile: Responsive desktop/mobile cơ bản.

## 10. Các vấn đề mở

<!-- Các mục cần được con người quyết định trước khi bắt đầu triển khai. -->

| #    | Câu hỏi | Người phụ trách | Hạn chót |
| ---- | ------- | --------------- | -------- |
| OI-1 | Ticket ID chưa được cung cấp. | q_hiep | không cần id ticket |
| OI-2 | Source nêu Frontend dùng Tailwind CSS | q_hiep | Đã chốt Tailwind CSS |
| OI-3 | Source nêu AI / Rule Engine MVP có thể dùng rule-based analyzer cơ bản hoặc LLM API; khuyến nghị kết hợp rule-based checks + LLM prompt review. Cần quyết định cấu hình triển khai cuối cùng. | [MISSING] | Đã chốt sử dụng cả 2 |
| OI-4 | Source nêu có thể deploy backend trên Vercel Python Runtime / Serverless Functions; cần xác nhận target deployment chính thức. | [MISSING] | Cần phải build được trên vercel |
| OI-5 | `AI_MODEL` chưa có giá trị cụ thể. | [MISSING] | hiện tại sủ dụng GROQ |
| OI-6 | Source không cung cấp schema/index thực tế; optimized query phụ thuộc schema thực tế. | [MISSING] | sẽ cung cấp schema/index để dễ tối ưu |

## 11. Rủi ro

| #   | Rủi ro | Khả năng xảy ra | Mức độ ảnh hưởng | Biện pháp giảm thiểu |
| --- | ------ | --------------- | ---------------- | -------------------- |
| 1   | AI hallucination schema | [MISSING] | High | Bắt AI nêu assumption rõ ràng |
| 2   | Query nhạy cảm | [MISSING] | High | Không lưu query mặc định |
| 3   | Serverless timeout | [MISSING] | Medium | Giới hạn input, timeout AI call |
| 4   | Review không chính xác | [MISSING] | Medium | Kết hợp rule-based + disclaimer |
| 5   | NoSQL đa dạng cú pháp | [MISSING] | Medium | MVP hỗ trợ MongoDB trước |

---

## Bảng truy vết

| #   | AC                | Màn hình/API | DB  | Logs | Quyền | Loại kiểm thử |
| --- | ----------------- | ------------ | --- | ---- | ----- | ------------- |
| 1   | AC-query-review-1/v1 | `/api/health` | [MISSING] | [MISSING] | [MISSING] | IT |
| 2   | AC-query-review-2/v1 | `/api/review` | [MISSING] | [MISSING] | [MISSING] | IT |
| 3   | AC-query-review-3/v1 | `/api/review` | [MISSING] | [MISSING] | [MISSING] | UT · IT |
| 4   | AC-query-review-4/v1 | `/api/review` | [MISSING] | [MISSING] | [MISSING] | UT · IT |
| 5   | AC-query-review-5/v1 | `/api/review` | [MISSING] | [MISSING] | [MISSING] | IT |
| 6   | AC-query-review-6/v1 | `rule_analyzer.py` | [MISSING] | [MISSING] | [MISSING] | UT |
| 7   | AC-query-review-7/v1 | `ai_reviewer.py` / Environment Variables | [MISSING] | [MISSING] | [MISSING] | UT · IT |
| 8   | AC-query-review-8/v1 | Màn hình chính / `QueryInput.tsx` | [MISSING] | [MISSING] | [MISSING] | E2E |
| 9   | AC-query-review-9/v1 | Màn hình chính / `ReviewResult.tsx` | [MISSING] | [MISSING] | [MISSING] | E2E |
| 10   | AC-query-review-10/v1 | Màn hình chính / `ReviewResult.tsx` | [MISSING] | [MISSING] | [MISSING] | E2E |
| 11   | AC-query-review-11/v1 | Frontend MVP | [MISSING] | [MISSING] | [MISSING] | E2E |
| 12   | AC-query-review-12/v1 | Local development | [MISSING] | [MISSING] | [MISSING] | BB |
| 13   | AC-query-review-13/v1 | Vercel deployment design | [MISSING] | [MISSING] | [MISSING] | BB |
| 14   | AC-query-review-14/v1 | Frontend / Environment Variables | [MISSING] | [MISSING] | [MISSING] | BB |
| 15   | AC-query-review-15/v1 | MVP end-to-end | [MISSING] | [MISSING] | [MISSING] | E2E · BB |
