# FeaturePilot — Intelligent Auto Data Structuring Platform (Phase 1)

Phase 1 lets you **upload** CSV, Excel, or JSON files and get **automatic schema detection**, **cleaning** (missing values, duplicates), and **download** of the cleaned dataset.

---

## What’s included

### Backend (FastAPI)
- **File handler**: CSV, Excel (.xlsx, .xls), JSON → Pandas DataFrame (with size/row limits).
- **Schema detector**: Numeric, categorical, datetime, text, boolean; currency/percentage parsing (e.g. `₹5000`, `45%`).
- **Cleaner**: Remove duplicates; fill missing (median for numeric, mode for categorical); standardize column names.
- **API**: `POST /upload` (returns schema, missing summary, stats, preview + `download_id`), `GET /download?download_id=...` (cleaned CSV).

### Frontend (React + Vite + Tailwind)
- Dark dashboard with drag-and-drop upload, progress, schema table, missing-value summary, summary cards, preview table, and **Download cleaned CSV**.

---

## Prerequisites

- **Python 3.10+** (3.11 or 3.12 recommended; see [Troubleshooting](#troubleshooting) if you use 3.14)
- **Node.js 18+** and npm

---

## 1. Backend setup and run

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

### If `pip install` fails (e.g. pydantic-core / Rust error on Python 3.14)

- **Option A — Use Python 3.11 or 3.12 (recommended):**  
  Install from [python.org](https://www.python.org/downloads/), then create the venv with that version:
  ```bash
  py -3.12 -m venv venv
  .\venv\Scripts\activate
  pip install -r requirements.txt
  ```
- **Option B — Keep Python 3.14:**  
  Install [Rust](https://rustup.rs/), **restart your terminal** so `cargo` is on PATH, then run `pip install -r requirements.txt` again from the project’s `backend` folder.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `pydantic-core` / "Cargo ... is not on PATH" | You’re likely on **Python 3.14**. Use **Python 3.12** (Option A above) or install Rust and restart the terminal (Option B). |
| "No module named 'app'" when running uvicorn | Run uvicorn from the `backend` directory: `cd backend` then `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`. |

---

Run the API (from the `backend` directory):

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  

---

## 2. Frontend setup and run

```bash
cd frontend
npm install
npm run dev
```

- App: http://localhost:5173  

The app uses `http://localhost:8000` by default. To override, create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

---

## 3. Step-by-step usage

1. **Start backend** (from `backend`): `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. **Start frontend** (from `frontend`): `npm run dev`
3. Open http://localhost:5173
4. **Upload** a CSV, Excel, or JSON file (drag & drop or click).
5. After processing you’ll see:
   - Summary cards (rows, columns, duplicates removed, missing filled)
   - Schema summary (column types and samples)
   - Missing value summary (count, %, fill strategy)
   - Preview (first 20 rows)
6. Click **Download cleaned CSV** to get the cleaned file.

---

## Project layout

```
FeaturePilot/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   └── upload.py
│   │   ├── services/
│   │   │   ├── schema_detector.py
│   │   │   ├── cleaner.py
│   │   │   ├── file_handler.py
│   │   │   └── analyzer.py
│   │   ├── models/
│   │   │   └── response_models.py
│   │   └── utils/
│   │       └── helpers.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.jsx
│   │   │   ├── SchemaTable.jsx
│   │   │   ├── PreviewTable.jsx
│   │   │   ├── SummaryCards.jsx
│   │   │   └── MissingValueSummary.jsx
│   │   ├── pages/
│   │   │   └── Dashboard.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
└── README.md
```

---

## Environment

- **Backend**: No env vars required for local run. Optional: adjust `MAX_FILE_SIZE_MB` / `MAX_ROWS` in `app/services/file_handler.py` if needed.
- **Frontend**: Optional `frontend/.env`: `VITE_API_URL=http://localhost:8000` (or your API URL).

---

## API summary

| Method | Endpoint    | Description |
|--------|-------------|-------------|
| POST   | `/upload`   | Upload file; returns schema, missing summary, stats, preview, `download_id`. |
| GET    | `/download` | Query `?download_id=<id>` (optional); returns cleaned CSV. |
| GET    | `/health`   | Health check. |

---

## Large file handling

- Backend limits: 50 MB and 500,000 rows by default (see `backend/app/services/file_handler.py`).
- Upload timeout on the frontend is 2 minutes (`frontend/src/services/api.js`).
