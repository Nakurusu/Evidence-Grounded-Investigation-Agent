# Development Roadmap

## Phase 1 - Foundation ✅

- FastAPI setup
- Upload API
- Background tasks
- PostgreSQL + SQLAlchemy + Alembic
- Logging + Validation
- Pipeline architecture

**Status**: Completed

---

## Phase 2 - Data Understanding ✅

- Data profiling
- Column type inference
- Identifier detection
- Missing value analysis
- Cardinality detection

**Outputs**: Data Profile Report

**Status**: Completed

---

## Phase 3 - Signal Detection ✅

- Outlier detection (IQR method)
- Identifier detection
- Trend detection (first-vs-last)
- Concentration analysis
- Distribution analysis (skew, variance)

8 signal types total.

**Outputs**: Signal Report

**Status**: Completed

---

## Phase 4 - Question Generation ✅

- Signal → investigation question mapping
- Question bank pattern
- Priority mapping from signal severity

**Outputs**: Investigation Questions

**Status**: Completed

---

## Phase 5 - Hypothesis Generation ✅

- Simple hypotheses (1 signal → 1 hypothesis)
- Composite hypotheses (2+ co-occurring signals)
- Confidence mapping from signal severity

**Outputs**: Ranked Hypotheses

**Status**: Completed

---

## Phase 6 - Evidence-Based Investigation ✅

- 7 evidence builders (registry pattern)
- Per-signal-type evidence extraction
- Hypothesis validation (supporting / refuting / inconclusive)
- Investigation report with templated findings
- Executive summary + next steps

**Outputs**: Investigation Report

**Status**: Completed

---

## Phase 7 - LLM Integration ✅

- `NarrativeGenerator` Protocol (provider-agnostic)
- `MockNarrativeGenerator` (deterministic, no API calls)
- Versioned prompt contracts (`app/prompts/`)
- `AIInvestigationReport` wrapper schema
- `Narrative` + `ModelMetadata` output structure
- Provider factory (`LLM_MODE` config)

Future: Anthropic SDK, OpenAI, etc. behind same Protocol.

**Outputs**: AI Investigation Report

**Status**: Completed

---

## Phase 8 - Interactive Investigation ✅

- Follow-up questions (drill-down, cross-pattern, alternative explanations)
- Data gap identification (missing data → weaker conclusions)
- Guided investigation paths (step-by-step exploration)
- Unresolved area tracking (inconclusive hypotheses)
- `InteractiveInvestigationReport` schema

**Outputs**: Interactive Investigation Report

**Status**: Completed

---

## Phase 9 - Multi-Dataset Analysis

- Cross-dataset reasoning
- Root-cause exploration
- Relationship discovery
- Investigation graph

**Outputs**: Investigation Graph

**Status**: Planned

---

## Phase 10 - Deployment & Operations

- Docker Compose setup
- API documentation (OpenAPI)
- CI/CD pipeline
- Demo dataset + example output

**Status**: Planned

---

## Summary

| Phase | Status |
|---|---|
| Phase 1 – Infrastructure | ✅ |
| Phase 2 – Dataset Profiling | ✅ |
| Phase 3 – Signal Detection | ✅ |
| Phase 4 – Question Generation | ✅ |
| Phase 5 – Hypothesis Generation | ✅ |
| Phase 6 – Evidence-Based Investigation | ✅ |
| Phase 7 – LLM Integration | ✅ |
| Phase 8 – Interactive Investigation | ✅ |
| Phase 9 – Multi-Dataset Analysis | ⏳ |
| Phase 10 – Deployment & Operations | ⏳ |

### Test Coverage

162 tests, 23 fixtures, covering:
- All 8 signal detectors
- All 7 evidence builders
- Hypothesis validation rules
- Report generation templates
- Narrative mock generator
- Interactive investigator
- Full pipeline integration
