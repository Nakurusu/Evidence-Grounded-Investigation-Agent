# System Architecture

## High-Level Flow

Data
↓
Data Quality Assessment
↓
Data Understanding
↓
Signal Detection
↓
Question Generation
↓
Hypothesis Generation
↓
Evidence Collection
↓
Investigation Engine
↓
Conclusion Generation
↓
Next Data Recommendation

---

## Components

### Data Quality Assessment

Purpose:

Determine whether data is trustworthy.

Checks:

- Missing values
- Duplicate rows
- Invalid types
- Outliers
- Coverage issues

---

### Data Understanding

Purpose:

Understand dataset structure.

Outputs:

- Row count
- Column count
- Column types
- Time range
- Unique values

Future:

- Schema understanding
- Semantic field recognition

---

### Signal Detection

Purpose:

Identify investigation-worthy signals.

Examples:

- Sudden changes
- Trends
- Distribution shifts
- Concentration risks
- Data quality issues

---

### Question Generation

Convert signals into investigation questions.

Example:

Revenue dropped 20%.

↓

Why did revenue drop 20%?

---

### Hypothesis Generation

Generate potential explanations.

Example:

Revenue decline:

- Product decline
- Regional decline
- Customer decline
- Pricing changes

---

### Evidence Collection

Collect supporting evidence.

Examples:

- Dimension contribution
- Segment contribution
- Trend breakdown

---

### Investigation Engine

Combines:

- Questions
- Hypotheses
- Evidence

Produces:

- Investigation reports

---

### Recommendation Engine

Identifies missing information.

Suggests:

- Inventory data
- Marketing data
- Pricing data
- Customer data

for deeper analysis.