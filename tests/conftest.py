"""Shared test fixtures for the investigative data analyst test suite.

Each fixture constructs a small pandas DataFrame designed to trigger a
specific signal type or pipeline behavior.  This keeps individual test
files focused on assertions rather than data construction.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta


# ═══════════════════════════════════════════════════════════════════════
# Minimal / edge-case datasets
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def empty_df() -> pd.DataFrame:
    """A DataFrame with columns but zero rows."""
    return pd.DataFrame({"a": [], "b": []})


@pytest.fixture
def single_row_df() -> pd.DataFrame:
    """A DataFrame with exactly one row."""
    return pd.DataFrame({"x": [1], "y": ["hello"]})


@pytest.fixture
def single_column_df() -> pd.DataFrame:
    """A DataFrame with one numeric column."""
    return pd.DataFrame({"value": [10, 20, 30, 40, 50]})


# ═══════════════════════════════════════════════════════════════════════
# Column-type datasets
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def mixed_types_df() -> pd.DataFrame:
    """One column of each type — used by profiler tests."""
    return pd.DataFrame(
        {
            "num_col": [1.0, 2.5, 3.0, 4.5, 5.0],
            "cat_col": ["a", "b", "a", "c", "b"],
            "text_col": [
                "apple banana",
                "cat dog",
                "elephant",
                "fox giraffe",
                "hello world",
            ],
            "date_col": pd.to_datetime(
                ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]
            ),
            "bool_col": [True, False, True, True, False],
        }
    )


@pytest.fixture
def id_column_df() -> pd.DataFrame:
    """A DataFrame with an obvious identifier column."""
    return pd.DataFrame(
        {
            "customer_id": [f"ID-{i:04d}" for i in range(100)],
            "value": list(range(100)),
        }
    )


# ═══════════════════════════════════════════════════════════════════════
# Signal-specific datasets
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def missing_rate_df() -> pd.DataFrame:
    """~25% missing values in col_a (should trigger HIGH_MISSING_RATE)."""
    return pd.DataFrame(
        {
            "col_a": [1.0, None, 3.0, None, 5.0, 6.0, None, 8.0],
            "col_b": [10, 20, 30, 40, 50, 60, 70, 80],
        }
    )


@pytest.fixture
def low_missing_rate_df() -> pd.DataFrame:
    """~12.5% missing — below the 20% threshold."""
    return pd.DataFrame(
        {
            "col_a": [1.0, None, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        }
    )


@pytest.fixture
def high_cardinality_df() -> pd.DataFrame:
    """A text column with >90% unique values."""
    return pd.DataFrame(
        {
            "col_a": [f"val_{i}" for i in range(100)],
        }
    )


@pytest.fixture
def low_cardinality_df() -> pd.DataFrame:
    """A text column with few unique values."""
    return pd.DataFrame(
        {
            "col_a": ["a", "b", "a", "b", "a", "c", "a", "b"] * 12,
        }
    )


@pytest.fixture
def outlier_df() -> pd.DataFrame:
    """Revenue column with clear IQR outliers.

    With 100 tightly clustered normal values plus 3 extreme outliers,
    the IQR method reliably detects the outliers.
    """
    normal = [100 + (i % 10) for i in range(100)]
    outliers = [500, 750, 1000]
    return pd.DataFrame({"revenue": normal + outliers})


@pytest.fixture
def no_outlier_df() -> pd.DataFrame:
    """Tightly clustered data — no IQR outliers."""
    return pd.DataFrame(
        {
            "revenue": [100, 102, 101, 99, 100, 101, 102, 98],
        }
    )


@pytest.fixture
def increasing_trend_df() -> pd.DataFrame:
    """Increasing numeric trend over time."""
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(10)]
    return pd.DataFrame(
        {
            "date": dates,
            "sales": [100, 110, 120, 130, 140, 150, 160, 170, 180, 190],
        }
    )


@pytest.fixture
def decreasing_trend_df() -> pd.DataFrame:
    """Decreasing numeric trend over time."""
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(10)]
    return pd.DataFrame(
        {
            "date": dates,
            "sales": [190, 180, 170, 160, 150, 140, 130, 120, 110, 100],
        }
    )


@pytest.fixture
def flat_trend_df() -> pd.DataFrame:
    """No meaningful trend — first ≈ last."""
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(10)]
    return pd.DataFrame(
        {
            "date": dates,
            "sales": [100, 105, 98, 102, 101, 99, 103, 100, 102, 101],
        }
    )


@pytest.fixture
def concentration_df() -> pd.DataFrame:
    """Revenue highly concentrated in one category."""
    return pd.DataFrame(
        {
            "category": ["A"] * 90 + ["B"] * 5 + ["C"] * 5,
            "revenue": [100] * 90 + [5] * 5 + [3] * 5,
        }
    )


@pytest.fixture
def no_concentration_df() -> pd.DataFrame:
    """Revenue evenly distributed across categories."""
    return pd.DataFrame(
        {
            "category": ["A"] * 33 + ["B"] * 33 + ["C"] * 34,
            "revenue": [100] * 33 + [100] * 33 + [100] * 34,
        }
    )


@pytest.fixture
def right_skewed_df() -> pd.DataFrame:
    """Mean significantly higher than median."""
    return pd.DataFrame(
        {
            "value": [1, 2, 3, 4, 5, 6, 7, 8, 9, 100],
        }
    )


@pytest.fixture
def left_skewed_df() -> pd.DataFrame:
    """Mean significantly lower than median (left-skewed).

    Multiple very low values pull the mean (< 74) well below the median (~92.5).
    mean < median * 0.8 → detected as LEFT_SKEWED.
    """
    return pd.DataFrame(
        {
            "value": [1, 1, 1, 5, 10, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100],
        }
    )


@pytest.fixture
def symmetric_df() -> pd.DataFrame:
    """Mean ≈ median."""
    return pd.DataFrame(
        {
            "value": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        }
    )


@pytest.fixture
def low_variance_df() -> pd.DataFrame:
    """Coefficient of variation < 5%."""
    return pd.DataFrame(
        {
            "price": [9.99] * 50 + [10.00] * 50,
        }
    )


@pytest.fixture
def normal_variance_df() -> pd.DataFrame:
    """Coefficient of variation > 10%."""
    return pd.DataFrame(
        {
            "value": [1, 10, 20, 30, 40, 50, 60, 70, 80, 100],
        }
    )


# ═══════════════════════════════════════════════════════════════════════
# Multi-signal integration dataset
# ═══════════════════════════════════════════════════════════════════════


@pytest.fixture
def integration_df() -> pd.DataFrame:
    """A realistic dataset that triggers multiple signal types.

    Designed to produce: outliers, right skew, increasing trend,
    high concentration, low variance, and ~20% missing rate.
    """
    n = 100
    dates = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(n)]

    # Revenue: right-skewed with outliers
    revenue = [100 + i * 2 for i in range(n)]  # mild trend
    revenue[0] = 5000  # outlier
    revenue[1] = 4500  # outlier

    # Units: increasing trend
    units = [10 + i // 2 for i in range(n)]

    # Price: very low variance
    price = [9.99 + (i % 3) * 0.005 for i in range(n)]

    # Category for concentration
    category = (
        ["Widget"] * 75 + ["Gadget"] * 15 + ["Doohickey"] * 10
    )

    # Rating with missing values
    rating = [4.5] * 100
    for i in range(25):  # 25% missing
        rating[i] = None

    return pd.DataFrame(
        {
            "date": dates,
            "category": category,
            "revenue": revenue,
            "units": units,
            "price": price,
            "rating": rating,
        }
    )
