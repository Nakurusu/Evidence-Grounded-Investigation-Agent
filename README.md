# Investigative Data Analyst

> An AI-powered investigation engine for structured business datasets.

Investigative Data Analyst is an AI Agent designed to help users investigate business problems from structured datasets.

Unlike traditional Business Intelligence (BI) dashboards or AutoEDA tools, this project focuses on **reasoning**, **evidence collection**, and **hypothesis validation**, guiding users through a structured investigation workflow instead of simply presenting descriptive statistics.

The long-term goal is to build an AI analyst capable of discovering anomalies, asking meaningful questions, validating hypotheses with evidence, and producing explainable investigation reports.

---

# Motivation

Most data analysis tools answer questions like:

- What happened?
- How many?
- Which category is the largest?

Investigative Data Analyst aims to answer deeper questions such as:

- Why did this happen?
- What evidence supports this conclusion?
- What should be investigated next?
- Which hypotheses are most likely to explain the observed signals?

The project combines deterministic statistical analysis with AI reasoning to simulate the workflow of an experienced business analyst.

---

# Features

## Completed

- Dataset profiling
- Automatic column type inference
- Identifier detection
- Missing value analysis
- Cardinality detection
- Outlier detection
- Trend detection
- Distribution analysis
- Concentration analysis
- Investigation question generation
- Hypothesis generation
- Modular investigation pipeline

## In Progress

- Evidence generation
- Investigation report generation

## Planned

- LLM-powered investigation reports
- Executive summaries
- Interactive investigation workflow
- Follow-up question generation
- Multi-dataset analysis
- Root-cause exploration
- Investigation graph

---

# Investigation Pipeline

```text
Dataset
    ↓
Dataset Profiling
    ↓
Signal Detection
    ↓
Question Generation
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

Each stage transforms the output of the previous stage into a higher level of business understanding.

---

# Project Structure

```text
app/
├── api/
│   └── FastAPI endpoints
│
├── models/
│   └── Enumerations
│
├── schemas/
│   └── Data models
│
├── services/
│   ├── profiler
│   ├── signal detector
│   ├── question generator
│   ├── hypothesis generator
│   └── evidence generator
│
└── main.py

docs/
├── architecture.md
├── principles.md
├── roadmap.md
├── vision.md
└── architecture_decisions.md
```

---

# Tech Stack

- Python
- FastAPI
- Pandas
- Pydantic
- PostgreSQL
- Alembic

Planned:

- OpenAI / Anthropic
- LangGraph
- LangSmith
- Docker

---

# Design Principles

The project is built around several core principles:

- Investigation before reporting
- Evidence-based reasoning
- Explainability
- Extensible architecture
- Separation of responsibilities
- Registry-based extensibility
- Deterministic analysis before LLM reasoning

For detailed design decisions, see the documentation in the `docs/` directory.

---

# Roadmap

| Phase | Status |
|--------|--------|
| Phase 1 – Infrastructure | ✅ |
| Phase 2 – Dataset Profiling | ✅ |
| Phase 3 – Signal Detection | ✅ |
| Phase 4 – Question Generation | ✅ |
| Phase 5 – Hypothesis Generation | ✅ |
| Phase 6 – Evidence-Based Investigation | ✅ |
| Phase 7 – LLM Integration | ⏳ |
| Phase 8 – Interactive Investigation | ⏳ |
| Phase 9 – Multi-Dataset Analysis | ⏳ |

---

# Quick Start

Clone the repository:

```bash
git clone https://github.com/Nakurusu/Investigative-Data-Analyst.git
cd Investigative-Data-Analyst
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run database migrations:

```bash
alembic upgrade head
```

Start the development server:

```bash
uvicorn app.main:app --reload
```

---

# Documentation

Project documentation is available under the `docs/` directory.

- **Vision** – Long-term project goals
- **Architecture** – System architecture and pipeline
- **Principles** – Engineering and design principles
- **Roadmap** – Development plan
- **Architecture Decisions** – Important design decisions

---

# Current Status

The project is currently focused on building the core investigation engine.

Current development work includes:

- Evidence generation
- Investigation reports
- Preparation for LLM integration

---

# Future Vision

The long-term objective is to evolve Investigative Data Analyst into a general-purpose AI investigation platform capable of:

- Business investigation
- Financial analysis
- Operational diagnostics
- Root-cause analysis
- Multi-dataset reasoning
- Human-AI collaborative investigation

---

# License

MIT License