# Running Investigative Data Analyst

Three ways to run the project — pick the one that fits your workflow.

---

## 1. CLI Demo (fastest — no server, no database)

Run the full pipeline on a built-in demo dataset.  Outputs formatted text to your terminal and saves a JSON report.

```bash
pip install -r requirements.txt

# Run on demo datasets:
python examples/run_investigation.py --demo sales       # revenue concentration + outliers
python examples/run_investigation.py --demo churn       # missing data + declining spend
python examples/run_investigation.py --demo operations  # low variance + sensor anomalies

# Run on your own CSV:
python examples/run_investigation.py path/to/data.csv
```

**Requirements**: Python 3.11, `pip install -r requirements.txt`.  No API keys needed when `LLM_MODE=mock`.

To use a real LLM for the narrative:

```bash
cp .env.example .env
# Edit .env: LLM_MODE=openai, LLM_API_KEY=your-key
python examples/run_investigation.py --demo sales
```

---

## 2. API Server (local development)

Launch the FastAPI server with file upload and background task processing.

```bash
# 1. Start PostgreSQL (e.g., via Docker):
docker compose up -d postgres

# 2. Set up the database:
cp .env.example .env
# Edit .env: set DATABASE_URL for your PostgreSQL

# 3. Run migrations + start server:
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive API documentation.

**Endpoints**:

| Method | Path | Description |
|---|---|---|
| `POST` | `/upload/` | Upload a CSV/Excel file, returns `task_id` |
| `GET`  | `/task/{task_id}` | Check task status and get results |

**Requirements**: Python 3.11, PostgreSQL.

---

## 3. Docker Compose (one command — no local Python required)

```bash
# Clone and configure:
cp .env.example .env
# Edit .env: set LLM_MODE and LLM_API_KEY if using a real LLM

# Start everything:
docker compose up -d

# Open API docs:
open http://localhost:8000/docs
```

This starts:
- **FastAPI** app on `http://localhost:8000`
- **PostgreSQL** on `localhost:5432`

Database migrations run automatically on startup.  Uploaded files and investigation results are persisted in Docker volumes.

**Requirements**: Docker.

---

## Demo Datasets

| File | Scenario | What It Shows |
|---|---|---|
| `demo_sales.csv` | 21-row multi-region sales data | Outliers (Premium products), right-skewed revenue, concentration risk, declining trend |
| `demo_churn.csv` | 22-row subscription churn data | Missing values (support tickets, last-active date), plan concentration, declining spend |
| `demo_operations.csv` | 20-row sensor monitoring data | Low variance (pressure), temperature outliers, normal/overheat status concentration |
