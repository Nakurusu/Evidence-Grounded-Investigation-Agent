# Investigative Data Analyst

> An AI-powered investigation engine that transforms structured datasets into evidence-based insights — not another dashboard, not another AutoEDA tool.

---

## What It Does

Drop in a CSV. Get back:

| Output | What It Tells You |
|---|---|
| **Signal Report** | What's interesting in the data? Outliers, trends, skew, concentration... |
| **Investigation Questions** | What should you ask next based on those signals? |
| **Hypotheses** | What might explain what you're seeing? |
| **Evidence** | What statistical evidence supports or refutes each hypothesis? |
| **Investigation Report** | Findings with business impact analysis and recommendations |
| **AI Narrative** | Natural-language summary (mock or LLM-powered) |
| **Interactive Investigation** | Follow-up questions, data gaps, step-by-step exploration paths |

---

## Quick Start (No Server, No API Keys)

```bash
pip install -r requirements.txt

# Run on a built-in demo scenario:
python examples/run_investigation.py --demo sales       # revenue concentration + outliers
python examples/run_investigation.py --demo churn       # missing data + declining spend
python examples/run_investigation.py --demo operations  # low variance + sensor anomalies

# Run on your own data:
python examples/run_investigation.py path/to/your_data.csv
```

This runs the **full pipeline** (all 8 phases) without needing FastAPI, PostgreSQL, or any LLM API keys. A JSON report is saved alongside the input CSV.

**Want to use a real LLM?**  Copy `.env.example` → `.env` and set your API key:

```bash
cp .env.example .env
# Edit .env: LLM_MODE=openai, LLM_API_KEY=sk-xxx
```

---

## Pipeline

```
CSV / Excel
    │
    ▼
┌──────────────────────────────────────────────────────┐
│  1. Profiler          column types, nulls, IDs       │
│  2. Signal Detector   8 signal types                 │
│  3. Question Gen      investigation questions        │
│  4. Hypothesis Gen    simple + composite             │
│  5. Evidence Builders 7 builders, registry pattern   │
│  6. Hypothesis Validator  supporting / refuting      │
│  7. Report Generator  findings + executive summary   │
│  8. AI Narrative      mock (now) → LLM (future)      │
│  9. Interactive       follow-ups, data gaps, paths   │
└──────────────────────────────────────────────────────┘
    │
    ▼
AIInvestigationReport (JSON)
```

See [docs/architecture.md](docs/architecture.md) for the full architecture and design decisions.

---

## Example Output

```
======================================================================
  INVESTIGATIVE DATA ANALYST — 200 rows × 6 columns
======================================================================

--- 2. SIGNALS DETECTED (5) ---
  [warning] outlier_detected    20 outliers detected in revenue
  [info   ] decreasing_trend    Column 'revenue' shows a decreasing trend
  [info   ] right_skewed        Column 'revenue' is right skewed

--- 6. VALIDATION — 6 supported, 0 refuted, 0 inconclusive ---

--- 8. AI NARRATIVE ---
  Investigation complete. 6 hypotheses tested: 6 supported.
  Overall risk: low with high confidence.

  Key Findings:
  • [SUPPORTED] revenue 存在异常值 (confidence: medium)
  • [SUPPORTED] 极端值可能正在影响整体结论 (confidence: medium)

--- 9. INTERACTIVE INVESTIGATION ---
  Follow-up Questions:
  • [high/cross_pattern] Are the detected outliers the CAUSE of the right skew?
  • [medium/drill_down] Do the outliers correlate with specific regions or periods?

  Data Gaps:
  • Customer segmentation data → CRM system
  • External benchmarks → Industry reports

  Investigation Paths:
  ▶ Investigate outlier records in revenue (5 steps)
  ▶ Diagnose the decline in revenue (6 steps)
```

---

## Project Structure

```
app/
├── api/              FastAPI endpoints (upload, tasks)
├── services/         Business logic
│   ├── profiler.py           column typing, identifiers
│   ├── signal_detector.py    8 signal types
│   ├── question_generator.py investigation questions
│   ├── hypothesis_generator.py  simple + composite
│   ├── evidence/             7 evidence builders (registry)
│   ├── hypothesis_validator.py  evidence classification
│   ├── report_generator.py   templated findings + exec summary
│   ├── narrative_generator.py  Protocol + Mock (Phase 7)
│   ├── interactive_investigator.py  follow-ups, gaps, paths (Phase 8)
│   └── pipeline.py           orchestrator
├── schemas/          Pure data models (Pydantic)
│   ├── ai_report.py          AIInvestigationReport, Narrative
│   ├── interactive.py        FollowUpQuestion, DataGap, InvestigationPath
│   └── ...
├── prompts/          Versioned prompt contracts (Phase 7)
│   ├── investigation_narrative.py
│   └── executive_brief.py
├── models/           Enums (SignalType, HypothesisStatus, ...)
└── core/             Settings, logging

tests/                162 tests, 23 fixtures
docs/                 Architecture, roadmap, decisions
examples/             Quick-start script
```

---

## Design Principles

- **Evidence before conclusions** — every finding references statistical evidence
- **Explainability** — traceable from claim → evidence → signal
- **Deterministic analysis first, LLM reasoning second** — stats are reproducible
- **Provider-agnostic** — LLM layer uses a Protocol; swap Anthropic/OpenAI/mock via config
- **Extensible** — registry pattern for signal detectors and evidence builders
- **Wrapping, not extending** — generative outputs wrap deterministic ones, never modify them

See [docs/principles.md](docs/principles.md) and [docs/decisions.md](docs/decisions.md) for the full rationale.

---

## Roadmap

| Phase | Status |
|---|---|
| Phase 1 – Infrastructure | ✅ |
| Phase 2 – Dataset Profiling | ✅ |
| Phase 3 – Signal Detection | ✅ |
| Phase 4 – Question Generation | ✅ |
| Phase 5 – Hypothesis Generation | ✅ |
| Phase 6 – Evidence-Based Investigation | ✅ |
| Phase 7 – LLM Integration (Protocol + Mock) | ✅ |
| Phase 8 – Interactive Investigation | ✅ |
| Phase 9 – Multi-Dataset Analysis | ⏳ |
| Phase 10 – Deployment & Operations | ⏳ |

See [docs/roadmap.md](docs/roadmap.md) for details.

---

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

**162 tests, 23 fixtures** covering all pipeline stages.

---

## Tech Stack

- Python 3.11+
- Pandas, Pydantic
- FastAPI, Uvicorn
- PostgreSQL, SQLAlchemy, Alembic
- pytest (162 tests)

Planned: Anthropic SDK, OpenAI SDK, Docker

---

## Documentation

- [Vision](docs/vision.md) — long-term project goals
- [Architecture](docs/architecture.md) — system design and pipeline flow
- [Principles](docs/principles.md) — product and engineering principles
- [Roadmap](docs/roadmap.md) — development phases
- [Decisions](docs/decisions.md) — important architecture decisions

---

## License

MIT
