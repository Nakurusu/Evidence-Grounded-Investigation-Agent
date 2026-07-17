"""Schemas for cross-dataset analysis — Phase 9.

These schemas describe relationships BETWEEN datasets, not within a single
dataset.  They sit above the single-dataset pipeline, consuming multiple
InvestigationReports and producing a graph of cross-dataset relationships.
"""

from pydantic import BaseModel


class CrossDatasetRelation(BaseModel):
    """A detected relationship between datasets.

    Each relation is deterministic — it's computed by comparing
    column profiles and signal reports, not by an LLM.
    """

    type: str
    """Relation type:
    - 'shared_dimension':         same-named column in both datasets
    - 'correlated_trend':         both datasets trend in the same direction
    - 'opposite_trend':           datasets trend in opposite directions
    - 'complementary_signal':     one has concentration, other has trend
    """

    description: str
    """Human-readable description of the relationship."""

    primary_context: str
    """What's happening in the primary dataset relevant to this relation."""

    secondary_context: str
    """What's happening in the secondary dataset relevant to this relation."""

    shared_columns: list[str] = []
    """Columns found in both datasets that are relevant to this relation."""

    confidence: str
    """'high', 'medium', or 'low' — how strong the evidence is."""


class InvestigationGraph(BaseModel):
    """A graph of cross-dataset relationships.

    Produced by the CrossDatasetAnalyzer.  Connects the primary dataset
    to one or more secondary datasets through shared dimensions,
    correlated trends, and complementary signals.

    This is the output of Phase 9 — it answers questions like:
    "How are these datasets related?" and "What cross-dataset hypotheses
    should I investigate?"
    """

    primary_dataset: str
    """Filename of the primary (investigation target) dataset."""

    secondary_datasets: list[str]
    """Filenames of the secondary (context) datasets."""

    shared_dimensions: list[str]
    """Column names that appear in BOTH the primary and at least one
    secondary dataset.  These are potential join keys or shared
    analytical dimensions."""

    relations: list[CrossDatasetRelation]
    """All detected cross-dataset relationships."""

    cross_hypotheses: list[str]
    """Natural-language hypotheses that span datasets.  Generated from
    template rules — e.g., 'Revenue decline in sales may be caused by
    churn in the East region (shared dimension: region).'"""
