# CLAUDE.md

# Investigative Data Analyst

## Overview

Investigative Data Analyst is an AI-powered investigation engine for structured datasets.

The goal is **not** to build another AutoEDA tool, BI dashboard, or visualization platform.

The goal is to help users investigate business problems by progressively transforming structured data into evidence-based insights.

The system should behave like an investigative analyst rather than a reporting tool.

---

# Investigation Workflow

The investigation pipeline follows this order:

```
Dataset
    ↓
Profile
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

Do not bypass intermediate stages.

Each stage should build upon the previous one.

---

# Project Vision

The system should answer questions such as:

- What happened?
- Why did it happen?
- What evidence supports this?
- What should be investigated next?
- What additional data would increase confidence?

The project focuses on investigation instead of reporting.

---

# Core Principles

## 1. Evidence Before Conclusions

Final conclusions should always be supported by evidence.

Avoid generating unsupported claims.

Evidence exists to validate or reject hypotheses.

---

## 2. Explainability

Every conclusion should be traceable back to:

- detected signals
- supporting evidence
- statistical calculations

Users should always understand why a conclusion was produced.

---

## 3. Extensibility

The architecture should make it easy to add new:

- signal detectors
- evidence builders
- generators
- report types

Prefer extension over modification.

---

## 4. Single Responsibility

Each module should have one responsibility.

Examples:

- profiler.py
    - dataset profiling

- signal_detector.py
    - signal detection

- question_generator.py
    - investigation questions

- evidence_generator.py
    - evidence extraction

Avoid combining multiple responsibilities.

---

## 5. Investigation First

Always prioritize investigation quality over feature quantity.

A smaller but well-designed investigation pipeline is preferred over many disconnected features.

---

# Architecture

The project follows a layered architecture.

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

Reports
```

Every layer consumes outputs from previous layers.

Avoid circular dependencies.

Business logic belongs inside `services`.

Schemas should remain pure data models.

---

# Coding Guidelines

Prefer:

- registry pattern
- composition over inheritance
- reusable builders
- pure helper functions
- explicit typing

Avoid:

- duplicated statistical calculations
- deeply nested if-else chains
- hard-coded thresholds throughout the codebase
- business logic inside schemas
- tightly coupled modules

When adding new functionality, prefer creating a new builder or generator rather than modifying unrelated modules.

---

# Current Development Phase

Current roadmap phase:

**Phase 7 – LLM Integration

Goals:

- Natural language summaries
- Investigation narratives
- Executive reports

Outputs:

- AI Investigation Report

---

# Future Roadmap

The remaining roadmap is:

Phase 7
- LLM Integration

Phase 8
- Interactive Investigation

Phase 9
- Multi-Dataset Analysis

Keep implementations compatible with future phases.

Avoid introducing designs that make these phases difficult to implement.

---

# Project Structure

```
app/

    api/
        FastAPI endpoints

    services/
        business logic

    schemas/
        data models

    models/
        enums

    prompts/
        LLM prompts

docs/
```

Responsibilities:

- services → business logic
- schemas → data structures only
- api → request handling
- prompts → prompt templates

---

# Development Philosophy

Prioritize:

1. Correctness
2. Explainability
3. Maintainability
4. Extensibility
5. Investigation Quality

Performance optimization should come after a clean architecture.

---

# Documentation

Long-term project documentation is maintained under:

- docs/vision.md
- docs/architecture.md
- docs/principles.md
- docs/roadmap.md
- docs/decisions.md

CLAUDE.md should remain concise and focus on development guidance.

Avoid duplicating documentation from the docs directory.

---

# Working Rules for Claude Code

When making changes:

- preserve existing architecture
- avoid unnecessary refactoring
- keep functions focused
- prefer incremental improvements
- explain significant architectural changes before implementing them

When suggesting new features:

- align with the project vision
- follow the investigation workflow
- consider future roadmap compatibility

When uncertain:

Favor architectural consistency over short-term convenience.

## Before Starting Any New Task

Always do the following before writing code:

1. Read CLAUDE.md
2. Read README.md
3. Read docs/architecture.md
4. Read docs/roadmap.md
5. Read docs/decisions.md
6. Read docs/vision.md
7. Read docs/principles.md
8. Understand the current pipeline implementation.
9. Summarize your understanding.
10. Propose an implementation plan.
11. Wait for confirmation before making architectural changes.