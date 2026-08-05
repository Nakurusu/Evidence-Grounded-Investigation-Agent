"""Tests for app/services/profiler.py — dataset profiling and column typing."""

import warnings

import pandas as pd
import pytest
from app.services.profiler import (
    profile_dataframe,
    infer_column_type,
    infer_semantic_role,
    detect_identifiers,
    unique_value_ratio,
)
from app.models.enums import ColumnSemanticRole, ColumnType
from app.schemas.profile import DatasetProfile


# ═══════════════════════════════════════════════════════════════════════
# Column type inference
# ═══════════════════════════════════════════════════════════════════════


class TestInferColumnType:
    def test_numeric_int(self):
        series = pd.Series([1, 2, 3, 4, 5])
        assert infer_column_type(series) == ColumnType.NUMERIC

    def test_numeric_float(self):
        series = pd.Series([1.0, 2.5, 3.7])
        assert infer_column_type(series) == ColumnType.NUMERIC

    def test_boolean(self):
        series = pd.Series([True, False, True])
        assert infer_column_type(series) == ColumnType.BOOLEAN

    def test_datetime(self):
        series = pd.to_datetime(pd.Series(["2024-01-01", "2024-06-15"]))
        assert infer_column_type(series) == ColumnType.DATETIME

    def test_datetime_string_inference(self):
        """String dates should be detected as DATETIME by parsing attempt."""
        series = pd.Series(["2024-01-01", "2024-02-01", "2024-03-01"])
        assert infer_column_type(series) == ColumnType.DATETIME

    def test_datetime_string_inference_does_not_warn(self):
        series = pd.Series(["2024-01-01", "2024-02-01", "2024-03-01"])
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            assert infer_column_type(series) == ColumnType.DATETIME
        assert caught == []

    def test_categorical_low_unique_ratio(self):
        """<50% unique → CATEGORICAL."""
        series = pd.Series(["a", "b", "a", "b", "a"])
        assert infer_column_type(series) == ColumnType.CATEGORICAL

    def test_text_high_unique_ratio(self):
        """>=50% unique → TEXT (if not datetime/numeric/bool)."""
        series = pd.Series(["w1", "w2", "w3", "w4"])
        assert infer_column_type(series) == ColumnType.TEXT

    def test_empty_series(self):
        """An entirely-NaN series should still return a type."""
        series = pd.Series([None, None, None])
        result = infer_column_type(series)
        assert result in ColumnType


# ═══════════════════════════════════════════════════════════════════════
# Unique value ratio
# ═══════════════════════════════════════════════════════════════════════


class TestUniqueValueRatio:
    def test_all_unique(self):
        assert unique_value_ratio(pd.Series([1, 2, 3, 4])) == 1.0

    def test_all_same(self):
        assert unique_value_ratio(pd.Series(["a", "a", "a"])) == pytest.approx(1 / 3)

    def test_empty_returns_zero(self):
        assert unique_value_ratio(pd.Series([], dtype=float)) == 0.0

    def test_with_nulls(self):
        """Nulls should be excluded from the calculation.

        After dropping NaN → [1, 1, 1], 1 unique / 3 total ≈ 0.333.
        """
        result = unique_value_ratio(pd.Series([1, 1, None, 1, None]))
        assert result == pytest.approx(1 / 3)


# ═══════════════════════════════════════════════════════════════════════
# Identifier detection
# ═══════════════════════════════════════════════════════════════════════


class TestDetectIdentifiers:
    def test_high_uniqueness_with_id_keyword(self):
        """>95% unique AND keyword 'id' → identifier."""
        series = pd.Series([f"ID-{i}" for i in range(100)])
        assert detect_identifiers("customer_id", series) is True

    def test_high_uniqueness_with_name_keyword(self):
        series = pd.Series([f"Person-{i}" for i in range(100)])
        assert detect_identifiers("product_name", series) is True

    def test_high_uniqueness_no_keyword(self):
        """>95% unique but no keyword → NOT an identifier."""
        series = pd.Series([f"X{i}" for i in range(100)])
        assert detect_identifiers("label", series) is False

    def test_low_uniqueness_with_keyword(self):
        """Low uniqueness → NOT an identifier even with keyword."""
        series = pd.Series(["a", "b", "a", "b"] * 25)
        assert detect_identifiers("some_id", series) is False

    @pytest.mark.parametrize("keyword", ["uuid", "key", "email", "phone", "account"])
    def test_identifier_keywords(self, keyword):
        series = pd.Series([f"v{i}" for i in range(100)])
        assert detect_identifiers(keyword, series) is True


# ═══════════════════════════════════════════════════════════════════════
# Profile structure
# ═══════════════════════════════════════════════════════════════════════


class TestProfileDataframe:
    def test_returns_dataset_profile(self, single_column_df):
        result = profile_dataframe(single_column_df)
        assert isinstance(result, DatasetProfile)

    def test_row_count(self, single_column_df):
        result = profile_dataframe(single_column_df)
        assert result.row_count == 5

    def test_column_count(self, single_column_df):
        result = profile_dataframe(single_column_df)
        assert result.column_count == 1

    def test_mixed_types_all_columns_present(self, mixed_types_df):
        result = profile_dataframe(mixed_types_df)
        names = {c.name for c in result.columns}
        assert names == {"num_col", "cat_col", "text_col", "date_col", "bool_col"}

    def test_null_count_correct(self):
        df = pd.DataFrame({"a": [1.0, None, 3.0, None, 5.0]})
        result = profile_dataframe(df)
        col = result.columns[0]
        assert col.null_count == 2
        assert col.null_percentage == 40.0

    def test_unique_count_correct(self, mixed_types_df):
        result = profile_dataframe(mixed_types_df)
        cat_col = next(c for c in result.columns if c.name == "cat_col")
        # cat_col = ["a", "b", "a", "c", "b"] → 3 unique
        assert cat_col.unique_count == 3

    def test_identifier_detected(self, id_column_df):
        result = profile_dataframe(id_column_df)
        id_col = next(c for c in result.columns if c.name == "customer_id")
        assert id_col.is_identifier is True

    def test_non_identifier(self, id_column_df):
        result = profile_dataframe(id_column_df)
        val_col = next(c for c in result.columns if c.name == "value")
        assert val_col.is_identifier is False

    def test_empty_dataframe_does_not_crash(self, empty_df):
        result = profile_dataframe(empty_df)
        assert result.row_count == 0
        assert result.column_count == 2

    def test_single_row(self, single_row_df):
        result = profile_dataframe(single_row_df)
        assert result.row_count == 1

    def test_profile_is_serializable(self, mixed_types_df):
        result = profile_dataframe(mixed_types_df)
        d = result.model_dump()
        assert d["row_count"] == 5
        assert len(d["columns"]) == 5

    def test_semantic_roles_are_assigned(self):
        df = pd.DataFrame(
            {
                "customer_id": [f"ID-{i}" for i in range(6)],
                "customer": [f"Customer {i}" for i in range(6)],
                "region": ["north", "south", "north", "west", "south", "north"],
                "date": pd.date_range("2024-01-01", periods=6),
                "revenue": [100, 120, 130, 140, 150, 160],
            }
        )

        result = profile_dataframe(df)
        roles = {column.name: column.semantic_role for column in result.columns}

        assert roles["customer_id"] == ColumnSemanticRole.IDENTIFIER
        assert roles["customer"] == ColumnSemanticRole.ENTITY
        assert roles["region"] == ColumnSemanticRole.DIMENSION
        assert roles["date"] == ColumnSemanticRole.TIME
        assert roles["revenue"] == ColumnSemanticRole.METRIC


class TestInferSemanticRole:
    def test_numeric_non_identifier_is_metric(self):
        role = infer_semantic_role(
            "revenue",
            pd.Series([1, 2, 3]),
            ColumnType.NUMERIC,
            False,
        )
        assert role == ColumnSemanticRole.METRIC

    def test_identifier_overrides_other_roles(self):
        role = infer_semantic_role(
            "customer_id",
            pd.Series(["A", "B", "C"]),
            ColumnType.TEXT,
            True,
        )
        assert role == ColumnSemanticRole.IDENTIFIER
