# Architecture Decisions

This document records important architectural and product decisions made during the development of Evidence-Grounded Investigation Agent.

The purpose of this document is to capture **why** decisions were made, rather than **what** was implemented.

Implementation details belong in code and documentation. This file preserves the reasoning behind major design choices.

---

# Decision 001

## Title

Investigation-first architecture

## Date

2026-07-09

## Status

Accepted

## Context

Many existing data analysis tools focus on descriptive statistics, dashboards, or automated exploratory data analysis (AutoEDA).

The goal of this project is different.

## Decision

Evidence-Grounded Investigation Agent is designed as an investigation engine rather than an AutoEDA tool.

The system should guide users through discovering, validating, and explaining business problems.

## Reason

The objective is to help users answer questions such as:

- What happened?
- Why did it happen?
- What evidence supports this?
- What should be investigated next?

instead of simply describing a dataset.

## Consequences

Future features should strengthen investigation capabilities rather than reporting capabilities.

---

# Decision 002

## Title

Evidence-based reasoning

## Date

2026-07-09

## Status

Accepted

## Context

Signals alone are not sufficient to justify business conclusions.

Hypotheses should be supported by measurable evidence.

## Decision

Evidence generation is an independent stage in the investigation pipeline.

Evidence exists to validate hypotheses before they appear in investigation reports.

## Reason

Separating evidence from hypotheses improves explainability and reduces unsupported conclusions.

This also prepares the system for future LLM reasoning.

## Consequences

Investigation reports should reference supporting evidence for every validated hypothesis.

Future LLM integrations should consume structured evidence instead of raw signals whenever possible.

---

# Decision 003

## Title

Layered investigation pipeline

## Date

2026-07-09

## Status

Accepted

## Context

The project consists of multiple analysis stages.

Each stage transforms information into a higher level of abstraction.

## Decision

The investigation pipeline follows a layered architecture:

```
Dataset
    ↓
Profile
    ↓
Signals
    ↓
Questions
    ↓
Evidence
    ↓
Hypotheses
    ↓
Investigation Report
```

Each stage consumes outputs from the previous stage.

## Reason

A layered pipeline improves modularity, explainability, and maintainability.

## Consequences

New functionality should integrate into the pipeline instead of bypassing existing stages.

---

# Decision 004

## Title

Registry-based extensibility

## Date

2026-07-09

## Status

Accepted

## Context

Signal types, evidence builders, and future generators will continue to grow.

Large conditional branches become difficult to maintain.

## Decision

Generators should use registry patterns whenever practical.

For example:

- Signal builders
- Evidence builders
- Future report generators

should register implementations instead of relying on large if-else chains.

## Reason

Registry-based designs improve extensibility and reduce modification of existing code.

## Consequences

Adding new investigation capabilities should primarily involve registering new builders.

---

# Decision 005

## Title

Explainability over automation

## Date

2026-07-09

## Status

Accepted

## Context

AI-generated conclusions are only valuable if users understand how they were produced.

## Decision

Every investigation result should remain traceable.

The relationship between:

- Signal
- Evidence
- Hypothesis

should always be preserved.

## Reason

Users should be able to understand and verify why a conclusion was generated.

## Consequences

Future reports and LLM summaries should reference supporting evidence whenever possible.

---

# Decision 006

## Title

Deterministic analysis before LLM reasoning

## Date

2026-07-09

## Status

Accepted

## Context

Statistical calculations should be reproducible and verifiable.

Large language models are better suited for interpretation than computation.

## Decision

Deterministic code is responsible for:

- profiling
- statistics
- signal detection
- evidence generation

LLMs are responsible for:

- reasoning
- summarization
- narrative generation
- executive reporting

## Reason

Separating computation from reasoning improves reliability and explainability.

## Consequences

Future LLM integrations should consume structured investigation outputs instead of raw datasets.

---

# Decision 007

## Title

Business logic separation

## Date

2026-07-09

## Status

Accepted

## Context

As the project grows, responsibilities should remain clearly separated.

## Decision

Schemas should only define data structures.

Business logic belongs inside services.

API layers should orchestrate workflows rather than perform analysis.

## Reason

Keeping responsibilities separate improves maintainability, testing, and future extensibility.

## Consequences

Schemas should not perform calculations.

Business rules should remain inside service modules.

---

# Decision 008

## Title

Deterministic reasoning and LLM responsibility separation

## Date

2026-07-09

## Status

Accepted

## Context

The project is evolving from a deterministic investigation engine into an AI-assisted investigation platform.

As LLM capabilities are introduced, it becomes important to clearly define which responsibilities belong to deterministic business logic and which belong to language models. Without this boundary, investigation results may become inconsistent, difficult to validate, and impossible to reproduce.

# Decision

All analytical reasoning must remain deterministic.

The deterministic investigation engine is responsible for:

* Dataset profiling
* Data quality assessment
* Signal detection
* Question generation
* Hypothesis generation
* Evidence collection
* Hypothesis validation
* Investigation report generation

LLMs are only responsible for presenting deterministic results in natural language.

Typical LLM responsibilities include:

* Investigation narratives
* Executive summaries
* Interactive explanations
* Report formatting
* Future conversational interfaces

LLMs must consume the InvestigationReport as input and must not generate or modify analytical conclusions independently.

# Reason

Separating reasoning from presentation provides several benefits:

* Investigation results remain reproducible.
* Analytical decisions remain explainable and auditable.
* Different LLM providers can be swapped without affecting business logic.
* The investigation engine can continue operating even when no LLM is available.
* Future presentation layers (Dashboard, PDF, Chat, API, etc.) can all consume the same deterministic InvestigationReport.

# Consequences

LLMs should explain findings, not produce findings.

Confidence scores, evidence, hypotheses, and validation results must always originate from deterministic services.

Natural language output should always be traceable back to the InvestigationReport.

Replacing an LLM provider should never require changes to the investigation engine itself.

---

# Decision 009

## Title

Structured InvestigationReport as single source of truth, all LLM output as Presentation Layer

## Date

2026-07-09

## Status

Accepted

## Context

The current architecture (v1.0) has the following division:

- **Deterministic**: profiling, signals, questions, hypotheses, evidence, validation, report findings (template-driven)
- **LLM Presentation Layer**: Narrative (executive summary, key findings, evidence summary, business impact, recommendations)

The report findings in `report_generator.py` (391 lines) and `report_templates.py` (748 lines) use Chinese templates to generate observation, analysis, business_impact, and recommendation text for each finding. This creates overlap with the LLM Narrative, which covers the same content but in a synthesized, data-aware form.

Looking ahead, more presentation forms are expected: executive briefs, interactive follow-up questions, data gap analysis, dashboard summaries, conversational interfaces. Each should consume the same structured data rather than duplicating logic.

## Decision

The `InvestigationReport` should evolve from a "report with embedded natural-language findings" into a **pure structured data contract**.

All natural-language output — Narrative, Executive Brief, Interactive follow-ups, future dashboard text, chat responses — should be generated by LLMs in the **Presentation Layer**, consuming the `InvestigationReport` as structured input.

Current templates in `report_generator.py`, `interactive_investigator.py`, and similar modules should be treated as **bootstrapping artifacts** — useful for initial development and mock mode, but not the long-term architecture.

**v1.0 (current)**:

```
InvestigationReport (template-driven findings)
    ├── Narrative (LLM) ← overlaps with findings
    └── Interactive (templates)
```

**v2.0 (target)**:

```
InvestigationReport (pure structured data: signals, evidence, stats)
    │
    ├── Narrative (LLM)
    ├── Executive Brief (LLM)
    ├── Interactive Follow-ups (LLM)
    ├── Dashboard Summary (LLM)
    └── ... future presentation forms ...
```

## Reason

- **Single source of truth**: Every presentation form derives from the same structured report, ensuring consistency.
- **No duplication**: Removing templates eliminates the need to maintain parallel text for each (SignalType × Status × Language) combination.
- **Provider flexibility**: All LLM interactions go through the same `NarrativeGenerator` Protocol — new presentation forms reuse the same infrastructure.
- **Incremental migration**: Templates remain functional in mock mode; LLM replaces them one presentation form at a time without breaking the pipeline.

## Consequences

- `report_generator.py` (391 lines) and `report_templates.py` (748 lines) remain in v1.0 but are marked for future decommissioning.
- `interactive_investigator.py` (642 lines) remains in v1.0 but is the first candidate for LLM replacement.
- New presentation forms (Executive Brief, etc.) should be LLM-native from the start.
- The `InvestigationReport` schema may need to grow richer structured fields (e.g., per-finding evidence summaries, segment breakdowns) to give LLMs enough data to generate high-quality output without templates.

---

# Decision 010

## Title

Transparent pipeline progress instead of hidden chain-of-thought

## Date

2026-08-04

## Status

Accepted

## Context

Users need to understand what the system is doing during long-running investigations.

However, the project separates deterministic investigation logic from LLM presentation. Showing or fabricating hidden model reasoning would blur that boundary and could imply unsupported causality.

## Decision

The product should display transparent investigation progress using deterministic pipeline stages.

Progress UI may show:

- current stage
- stage goal
- stage input
- stage output
- why the stage matters
- completed stages

Progress UI must not show or invent hidden LLM chain-of-thought.

## Reason

Stage-level transparency helps users understand that the system is progressively transforming data into evidence-backed findings.

It also preserves the architecture principle that conclusions must come from signals, evidence, validation, and structured reports rather than opaque model reasoning.

## Consequences

Task progress contracts should include user-facing stage explanations.

Frontend loading states should explain the deterministic investigation workflow.

LLM narrative failures should not invalidate completed deterministic reports.
