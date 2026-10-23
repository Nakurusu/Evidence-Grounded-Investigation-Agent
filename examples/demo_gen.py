"""Generate demo datasets for Evidence-Grounded Investigation Agent showcase.

Primary: retail revenue — triggers decreasing trend, high concentration, missing rate
Secondary: customer complaints — triggers increasing trend (opposite to revenue)
"""

import csv
from datetime import datetime, timedelta

# ── Primary: Retail Revenue ──────────────────────────────────────────
# 5 regions × 12 months = 60 rows
# Design:
#   - East: revenue 620→160 (dramatic decline, ~50% concentration)
#   - South/West/North/Central: relatively stable
#   - satisfaction_score: North mostly missing (9/12 blank)
#   - customer_count: correlated with revenue

months = [
    "2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06",
    "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12",
]

revenue = {
    "East":    [620, 600, 570, 540, 500, 460, 410, 360, 310, 260, 210, 160],
    "South":   [150, 148, 152, 145, 150, 148, 146, 150, 148, 152, 149, 151],
    "West":    [120, 118, 122, 119, 121, 120, 118, 122, 119, 121, 120, 118],
    "North":   [80, 82, 78, 80, 79, 81, 80, 78, 82, 80, 79, 81],
    "Central": [60, 58, 62, 60, 59, 61, 60, 58, 62, 60, 59, 61],
}

# customer_count roughly proportional to revenue
customer_count = {
    r: [max(30, int(v * 0.45 + (-5 if i % 3 == 0 else 5))) for i, v in enumerate(vals)]
    for r, vals in revenue.items()
}

# satisfaction_score: East/South/West/Central present, North mostly missing
satisfaction = {
    "East":    [4.2, 4.1, 4.0, 3.9, 3.8, 3.7, 3.5, 3.3, 3.1, 2.9, 2.7, 2.5],
    "South":   [3.9, 4.0, 3.8, 4.1, 3.9, 4.0, 3.8, 3.9, 4.0, 3.8, 3.9, 4.0],
    "West":    [4.1, 4.0, 4.2, 4.1, 4.0, 4.1, 4.2, 4.0, 4.1, 4.2, 4.0, 4.1],
    "North":   [None, 3.8, None, None, 3.5, None, None, None, 3.2, None, None, None],
    "Central": [3.7, 3.8, 3.6, 3.7, 3.8, 3.7, 3.6, 3.8, 3.7, 3.6, 3.8, 3.7],
}

with open("examples/demo_retail_revenue.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "region", "revenue", "customer_count", "satisfaction_score"])
    for month in months:
        for region in ["East", "South", "West", "North", "Central"]:
            idx = months.index(month)
            sat = satisfaction[region][idx]
            w.writerow([
                f"{month}-01",
                region,
                revenue[region][idx],
                customer_count[region][idx],
                sat if sat is not None else "",
            ])

# ── Secondary: Customer Complaints ────────────────────────────────────
# 5 regions × 12 months = 60 rows
# Design:
#   - complaint_count: increasing across all regions (opposite to revenue)
#   - East has the steepest increase
#   - avg_resolution_hours: increasing slightly

complaints = {
    "East":    [15, 18, 22, 28, 35, 42, 50, 58, 65, 72, 80, 88],
    "South":   [5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 11],
    "West":    [4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10],
    "North":   [3, 3, 4, 4, 5, 5, 6, 6, 7, 7, 8, 8],
    "Central": [2, 2, 3, 3, 3, 4, 4, 5, 5, 6, 6, 7],
}

resolution_hours = {
    "East":    [4.5, 4.8, 5.2, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5],
    "South":   [3.2, 3.3, 3.5, 3.4, 3.6, 3.5, 3.7, 3.6, 3.8, 3.7, 3.9, 3.8],
    "West":    [3.0, 3.1, 3.2, 3.0, 3.3, 3.1, 3.4, 3.2, 3.5, 3.3, 3.6, 3.4],
    "North":   [2.8, 2.9, 3.0, 2.8, 3.1, 2.9, 3.2, 3.0, 3.3, 3.1, 3.4, 3.2],
    "Central": [2.5, 2.6, 2.7, 2.5, 2.8, 2.6, 2.9, 2.7, 3.0, 2.8, 3.1, 2.9],
}

with open("examples/demo_customer_complaints.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "region", "complaint_count", "avg_resolution_hours"])
    for month in months:
        for region in ["East", "South", "West", "North", "Central"]:
            idx = months.index(month)
            w.writerow([
                f"{month}-01",
                region,
                complaints[region][idx],
                resolution_hours[region][idx],
            ])

print("Generated:")
print("  examples/demo_retail_revenue.csv (60 rows)")
print("  examples/demo_customer_complaints.csv (60 rows)")

# Quick stats
east_rev = sum(revenue["East"])
total_rev = sum(sum(v) for v in revenue.values())
print(f"\nPrimary stats:")
print(f"  East revenue share: {east_rev/total_rev:.1%}")
print(f"  East revenue decline: {revenue['East'][0]} → {revenue['East'][-1]} ({(revenue['East'][-1]/revenue['East'][0]-1)*100:.1f}%)")
print(f"  North missing satisfaction: {sum(1 for v in satisfaction['North'] if v is None)}/12")

east_comp = sum(complaints["East"])
total_comp = sum(sum(v) for v in complaints.values())
print(f"\nSecondary stats:")
print(f"  East complaint share: {east_comp/total_comp:.1%}")
print(f"  Complaint trend: {complaints['East'][0]} → {complaints['East'][-1]} (grew {complaints['East'][-1]/complaints['East'][0]-1:+.0%})")
