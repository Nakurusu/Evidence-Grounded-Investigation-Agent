# Investigative Data Analyst

An AI-powered investigation engine for structured datasets. It turns CSV or Excel data into evidence-backed findings, ranked cause candidates, natural-language summaries, and runnable follow-up analyses.

The project is built around investigation rather than reporting. It helps users narrow a business problem from raw data to signals, hypotheses, evidence, confidence notes, and the next questions worth checking.

## Current status

The MVP track is complete. The system now supports both exploration-driven analysis and question-driven investigation.

| Area | Status |
|---|---|
| Core pipeline, profiling, signal detection, hypotheses, evidence, validation | Complete |
| Question-aware investigation | Complete |
| Semantic field roles | Complete |
| Cause candidate ranking | Complete |
| Runnable follow-up analysis | Complete |
| LLM narrative layer with mock fallback | Complete |
| Multi-dataset investigation graph | Planned |

## What it does

Upload a structured dataset and, optionally, provide a business question such as “为什么收入下降？” or “哪些地区表现异常？”. The system returns a structured `AIInvestigationReport` containing:

| Output | Purpose |
|---|---|
| Dataset profile | Column types, semantic roles, missingness, identifiers |
| Signal report | Outliers, trends, skew, high concentration, high cardinality, low variance |
| Investigation questions | Questions generated from detected signals |
| Hypotheses | Simple and composite explanations for observed patterns |
| Evidence | Statistical evidence that supports, refutes, or weakens hypotheses |
| Findings | Business-readable findings with evidence strength and uncertainty notes |
| Cause candidates | 3 to 5 likely explanations ranked by deterministic evidence |
| AI narrative | Plain-language summary generated from the deterministic report |
| Interactive investigation | Follow-up questions, data gaps, investigation paths, and runnable drill-down results |

## Investigation flow

```text
CSV / Excel
    ↓
Parser + Normalizer
    ↓
Dataset Profile
    ↓
Signal Detection
    ↓
Question Generation
    ↓
Hypothesis Generation
    ↓
Evidence Generation
    ↓
Hypothesis Validation
    ↓
Investigation Report
    ↓
LLM Narrative
    ↓
Interactive Investigation
```

Every layer consumes outputs from previous layers. The system avoids letting LLMs invent analytical conclusions: deterministic services produce signals, evidence, confidence, and validation status; the LLM layer explains those results in natural language.

## MVP highlights

### Question-aware investigation

Users can add an optional investigation question at upload time. The question influences sorting and presentation without filtering out unrelated evidence or allowing the LLM to change deterministic conclusions.

### Semantic field roles

The profiler identifies analysis roles such as `metric`, `dimension`, `time`, `entity`, and `identifier`. These roles help the pipeline avoid treating IDs as ordinary dimensions and guide trend, concentration, and drill-down analyses.

### Cause candidate ranking

The report ranks likely explanations based on evidence count, confidence, question relevance, data-quality limitations, and whether multiple signals point to the same explanation. Candidates are written as hypotheses, not guaranteed root causes.

### Runnable follow-ups

Some follow-up questions can now run additional deterministic analysis against the original uploaded dataset. Results are appended to the interactive investigation layer and do not overwrite the original report.

Supported drill-down analyses:

| Signal family | Analysis type | What it checks |
|---|---|---|
| Outliers and skew | `tail_records` | Tail or outlier records and their contribution |
| Increasing or decreasing trend | `trend_by_dimension` | Which dimension groups drive the trend |
| High concentration | `top_category_vs_rest` | Top category contribution versus the rest |
| High missing rate | `missingness_by_dimension` | Whether missingness is concentrated in specific groups |
| High cardinality | `cardinality_distribution` | Value frequency distribution and coverage thresholds |
| Low variance | `low_variance_distribution` | Coefficient of variation and dominant values |

## Example

The repository includes `examples/high_cardinality_test.csv`, a small dataset designed to trigger high-cardinality detection on `sku_group`.

After uploading it with the question “这个字段唯一值是否过多，能否聚合？”, the pipeline detects:

```text
[SUPPORTED] sku_group 可能包含过多唯一值
unique_ratio = 1.0
```

Running the first follow-up question returns:

```text
analysis_type = cardinality_distribution
status = completed

字段 sku_group 共有 40 个唯一值。
前 10 个值覆盖了 40 条记录中的 25.0%。
前 32 个值已覆盖 80% 的记录，可考虑将其余值归为「其他」。
```

This demonstrates the complete MVP loop: upload data, ask a question, receive evidence-backed findings, then run a follow-up analysis.

## Quick start

### Run with Docker Compose

```bash
cp .env.example .env
docker compose up -d
```

The API will be available at:

```text
http://localhost:8000/docs
```

### Run locally

Use Python 3.11+ and PostgreSQL. The app reads configuration from `.env`.

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

For local development with a conda environment:

```bash
conda activate ai
alembic upgrade head
uvicorn app.main:app --reload
```

### CLI demo

```bash
python examples/run_investigation.py --demo sales
python examples/run_investigation.py --demo operations
python examples/run_investigation.py --demo churn
```

See [examples/README.md](examples/README.md) for more demo details.

## API usage

Upload a dataset:

```bash
curl -X POST "http://localhost:8000/upload/" \
  -F "file=@examples/high_cardinality_test.csv" \
  -F "investigation_question=这个字段唯一值是否过多，能否聚合？"
```

Fetch task result:

```bash
curl "http://localhost:8000/task/{task_id}"
```

Run a follow-up drill-down:

```bash
curl -X POST \
  "http://localhost:8000/task/{task_id}/follow-ups/{question_index}/drilldown"
```

The drill-down result is appended to:

```text
result.interactive_investigation.drilldown_steps
```

## Project structure

```text
app/
├── api/                 FastAPI endpoints
├── core/                Settings and logging
├── db/                  SQLAlchemy database setup
├── models/              ORM models and enums
├── prompts/             Versioned LLM prompt contracts
├── schemas/             Pydantic data contracts
└── services/            Investigation business logic
    ├── evidence/        Evidence builders
    ├── profiler.py
    ├── signal_detector.py
    ├── question_generator.py
    ├── hypothesis_generator.py
    ├── hypothesis_validator.py
    ├── cause_ranker.py
    ├── drilldown.py
    ├── report_generator.py
    ├── narrative_generator.py
    └── pipeline.py

frontend/
├── src/api/             API client and shared types
├── src/components/      UI components
├── src/i18n/            Chinese and English translations
├── src/pages/           Upload and investigation pages
└── src/hooks/           Polling, theme, upload hooks

docs/                    Vision, architecture, decisions, roadmap
examples/                Demo datasets and CLI examples
tests/                   Backend test suite
```

## Architecture principles

- Evidence before conclusions: every finding must trace back to structured evidence.
- Explainability: conclusions reference signals, methods, thresholds, sample sizes, and limitations.
- Deterministic analysis before LLM presentation: LLMs explain findings, not produce findings.
- Extension over modification: new detectors and builders should follow registry-style patterns where possible.
- Schemas stay pure: business logic belongs in `app/services`.
- Investigation quality comes before feature quantity.

## Tech stack

| Layer | Tools |
|---|---|
| Backend | Python 3.11+, FastAPI, Pandas, Pydantic |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| LLM integration | Provider-agnostic protocol, mock fallback, OpenAI-compatible mode |
| Frontend | React, TypeScript, Vite, i18n |
| Testing | pytest |
| Deployment | Docker Compose |

## Tests

```bash
python -m pytest tests/ -q
```

Current backend coverage:

```text
209 passed, 1 skipped
```

The test suite covers profiling, signal detection, evidence builders, hypothesis validation, report generation, narrative fallback, interactive investigation, and all six runnable drill-down analysis types.

## Documentation

- [Vision](docs/vision.md)
- [Architecture](docs/architecture.md)
- [Principles](docs/principles.md)
- [Roadmap](docs/roadmap.md)
- [Decisions](docs/decisions.md)
- [MVP Plan](docs/mvp-plan.md)

## License

MIT
