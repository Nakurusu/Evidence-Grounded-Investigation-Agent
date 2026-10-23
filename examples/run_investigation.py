#!/usr/bin/env python3
"""Quick-start example: run a full investigation on a CSV file.

Usage:
    python examples/run_investigation.py <path/to/data.csv>
    python examples/run_investigation.py --demo           # run on demo_sales.csv
    python examples/run_investigation.py --demo sales      # sales data
    python examples/run_investigation.py --demo churn      # customer churn data
    python examples/run_investigation.py --demo operations # operations metrics

Built-in demo scenarios:
    sales      — revenue concentration, right skew, outliers, trends
    churn      — missing data, decreasing spend, plan concentration
    operations — low variance, sensor outliers, high concentration

This script runs the COMPLETE investigation pipeline (Phase 1–8)
without needing FastAPI, PostgreSQL, or any LLM API keys.

What you get:
    1. Dataset Profile           — column types, nulls, cardinality
    2. Signals Detected          — outliers, trends, skew, concentration, etc.
    3. Investigation Report      — findings with evidence, business impact
    4. AI Narrative             — natural-language summary (mock or LLM)
    5. Interactive Investigation — follow-up questions, data gaps, next paths

Output is printed as formatted text AND saved as JSON.
"""

import json
import sys
import os
from datetime import datetime, timedelta

import pandas as pd

# Allow running from any directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.parser import parse_file
from app.services.normalizer import normalize_dataframe
from app.services.validator import validate_dataframe
from app.services.profiler import profile_dataframe
from app.services.signal_detector import detect_signals
from app.services.question_generator import generate_questions
from app.services.hypothesis_generator import generate_hypotheses
from app.services.evidence import generate_all_evidence
from app.services.hypothesis_validator import validate_hypotheses
from app.services.analyzer import analyze_dataframe
from app.services.report_generator import generate_report
from app.services.narrative_generator import get_narrative_generator
from app.services.interactive_investigator import InteractiveInvestigator
from app.schemas.ai_report import AIInvestigationReport


# ═══════════════════════════════════════════════════════════════════════════
# Built-in demo dataset
# ═══════════════════════════════════════════════════════════════════════════


def _resolve_demo(demo_name: str | None) -> str:
    """Return the path to a built-in demo CSV.

    Args:
        demo_name: 'sales', 'churn', 'operations', or None (defaults to 'sales').
    """
    name = demo_name or "sales"
    mapping = {
        "sales": "demo_sales.csv",
        "churn": "demo_churn.csv",
        "operations": "demo_operations.csv",
    }
    if name not in mapping:
        print(f"Unknown demo '{name}'.  Available: {', '.join(mapping.keys())}")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, mapping[name])


# ═══════════════════════════════════════════════════════════════════════════
# Formatted output
# ═══════════════════════════════════════════════════════════════════════════


SEP = "=" * 70
SUB = "-" * 70


def print_header(title: str):
    print(f"\n{SEP}\n  {title}\n{SEP}")


def print_section(title: str):
    print(f"\n{SUB}\n  {title}\n{SUB}")


def run(file_path: str):
    print_header("EVIDENCE-GROUNDED INVESTIGATION AGENT — FULL PIPELINE")
    print(f"  Source: {file_path}")

    # ── Parse & Validate ──────────────────────────────────────────────
    df = parse_file(file_path)
    df = normalize_dataframe(df)
    validate_dataframe(df)
    print(f"\n  Rows: {len(df):,}   Columns: {len(df.columns)}")

    # ── Profile ───────────────────────────────────────────────────────
    profile = profile_dataframe(df)
    print_section("1. DATASET PROFILE")
    for c in profile.columns:
        flags = []
        if c.is_identifier:
            flags.append("ID")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        print(
            f"  {c.name:20s}  {c.dtype.value:12s}  "
            f"null={c.null_percentage:5.1f}%  unique={c.unique_count}{flag_str}"
        )

    # ── Signals ───────────────────────────────────────────────────────
    signals = detect_signals(df, profile)
    print_section(f"2. SIGNALS DETECTED ({len(signals.signals)})")
    for s in signals.signals:
        print(f"  [{s.severity.value:7s}] {s.type.value:25s}  {s.message}")

    # ── Questions ─────────────────────────────────────────────────────
    questions = generate_questions(signals)
    print_section(f"3. INVESTIGATION QUESTIONS ({len(questions.questions)})")
    for q in questions.questions[:10]:
        print(f"  [{q.priority.value}] {q.question}")

    # ── Hypotheses ────────────────────────────────────────────────────
    hypotheses = generate_hypotheses(signals)
    simple = [h for h in hypotheses.hypotheses if not h.is_composite]
    composite = [h for h in hypotheses.hypotheses if h.is_composite]
    print_section(
        f"4. HYPOTHESES ({len(simple)} simple + {len(composite)} composite)"
    )
    for h in hypotheses.hypotheses:
        tag = "[COMPOSITE]" if h.is_composite else ""
        print(f"  {tag} [{h.confidence.value}] {h.title}")

    # ── Evidence ──────────────────────────────────────────────────────
    evidence = generate_all_evidence(df, profile, hypotheses, signals)
    total_ev = sum(len(e) for e in evidence)
    print_section(f"5. EVIDENCE ({total_ev} items)")

    # ── Validate ──────────────────────────────────────────────────────
    validation = validate_hypotheses(hypotheses, evidence)
    supported = [v for v in validation.validated if v.status.value == "supported"]
    refuted = [v for v in validation.validated if v.status.value == "refuted"]
    inconclusive = [
        v for v in validation.validated if v.status.value == "inconclusive"
    ]
    print_section(
        f"6. VALIDATION — {len(supported)} supported, "
        f"{len(refuted)} refuted, {len(inconclusive)} inconclusive"
    )

    # ── Report ────────────────────────────────────────────────────────
    summary = analyze_dataframe(df, profile)
    report = generate_report(validation, profile, summary)
    print_section("7. INVESTIGATION REPORT")
    es = report.executive_summary
    print(f"  Total Hypotheses: {es.total_hypotheses}")
    print(f"  Supported: {es.supported_count}  |  Refuted: {es.refuted_count}  |  Inconclusive: {es.inconclusive_count}")
    print(f"  Overall Risk: {es.overall_risk}  |  Confidence: {es.overall_confidence}")
    print(f"  Top Priorities: {', '.join(es.highest_priority_findings[:3]) or '(none)'}")

    for i, f in enumerate(report.findings, 1):
        print_section(f"  Finding {i}: {f.title}")
        print(f"  Status:     {f.status.value}  |  Confidence: {f.confidence.value}")
        print(f"  Finding:    {f.observation[:150]}")
        print(f"  Impact:     {f.business_impact[:150]}")
        print(f"  Action:     {f.recommendation[:150]}")

    # ── Narrative (mock) ──────────────────────────────────────────────
    gen = get_narrative_generator()
    narrative, metadata = gen.generate(report)
    print_section(f"8. AI NARRATIVE ({metadata.provider})")
    print(f"  Provider: {metadata.provider}  |  Model: {metadata.model_name}")
    print(f"  Prompt Version: {metadata.prompt_version}")
    print(f"\n  --- Executive Summary ---\n  {narrative.executive_summary[:300]}")
    print(f"\n  --- Key Findings ---")
    for kf in narrative.key_findings[:5]:
        print(f"  • {kf}")
    print(f"\n  --- Business Impact ---\n  {narrative.business_impact_summary[:300]}")
    print(f"\n  --- Recommendations ---")
    for r in narrative.recommendations[:5]:
        print(f"  • {r}")

    # ── Interactive ───────────────────────────────────────────────────
    investigator = InteractiveInvestigator()
    interactive = investigator.investigate(report)
    print_section("9. INTERACTIVE INVESTIGATION")
    print(f"  Follow-up Questions: {len(interactive.follow_up_questions)}")
    for q in interactive.follow_up_questions[:5]:
        print(f"  [{q.priority}/{q.category}] {q.question[:140]}")
    print(f"\n  Data Gaps: {len(interactive.data_gaps)}")
    for g in interactive.data_gaps[:3]:
        print(f"  • {g.gap}")
        print(f"    → {g.suggested_source}")
    print(f"\n  Investigation Paths: {len(interactive.investigation_paths)}")
    for p in interactive.investigation_paths[:3]:
        print(f"  ▶ {p.title}")
        print(f"    {len(p.steps)} steps")

    # ── Final output ──────────────────────────────────────────────────
    ai_report = AIInvestigationReport(
        investigation_report=report,
        narrative=narrative,
        model_metadata=metadata,
        interactive_investigation=interactive,
    )

    result = ai_report.model_dump()
    json_path = file_path.replace(".csv", "_investigation.json")
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    print(f"\n{SEP}")
    print(f"  ✅ Full report saved to: {json_path}")
    print(f"{SEP}\n")


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python examples/run_investigation.py <path/to/data.csv>")
        print("       python examples/run_investigation.py --demo [sales|churn|operations]")
        sys.exit(1)

    if sys.argv[1] == "--demo":
        demo_name = sys.argv[2] if len(sys.argv) > 2 else "sales"
        path = _resolve_demo(demo_name)
        scenario = os.path.basename(path).replace("demo_", "").replace(".csv", "")
        print(f"  📊 Demo scenario: {scenario}\n")
        run(path)
    else:
        run(sys.argv[1])
