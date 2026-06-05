"""报告数据分析：KPI、分布区间、DataFrame 转换。"""
from typing import Any

import pandas as pd

SCORE_BUCKETS = [
    ("90-100", 90, 100),
    ("80-89", 80, 89),
    ("70-79", 70, 79),
    ("60-69", 60, 69),
    ("0-59", 0, 59),
]


def cases_to_dataframe(report: dict[str, Any]) -> pd.DataFrame:
    cases = report.get("cases", [])
    if not cases:
        return pd.DataFrame(
            columns=[
                "case_id", "test_module", "mock_file",
                "prompt", "response", "score", "is_pass", "reason", "status",
            ]
        )
    return pd.DataFrame(cases)


def compute_average_score(df: pd.DataFrame) -> float:
    if df.empty or "score" not in df.columns:
        return 0.0
    numeric = pd.to_numeric(df["score"], errors="coerce").dropna()
    if numeric.empty:
        return 0.0
    return round(float(numeric.mean()), 2)


def score_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame({"区间": [], "数量": []})

    scores = pd.to_numeric(df["score"], errors="coerce")
    counts = {label: 0 for label, _, _ in SCORE_BUCKETS}
    no_score = 0

    for value in scores:
        if pd.isna(value):
            no_score += 1
            continue
        placed = False
        for label, low, high in SCORE_BUCKETS:
            if low <= value <= high:
                counts[label] += 1
                placed = True
                break
        if not placed:
            no_score += 1

    rows = [{"区间": label, "数量": counts[label]} for label, _, _ in SCORE_BUCKETS]
    if no_score:
        rows.append({"区间": "无分数", "数量": no_score})
    return pd.DataFrame(rows)


def status_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "status" not in df.columns:
        return pd.DataFrame({"状态": [], "数量": []})
    counts = df["status"].value_counts().reset_index()
    counts.columns = ["状态", "数量"]
    return counts


def failed_cases(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df[df["status"] == "FAIL"].copy()


def kpi_from_report(report: dict[str, Any], df: pd.DataFrame) -> dict[str, Any]:
    return {
        "total_cases": report.get("total_cases", len(df)),
        "pass_rate": report.get("pass_rate", 0.0),
        "pass_rate_pct": round(report.get("pass_rate", 0.0) * 100, 2),
        "avg_score": compute_average_score(df),
        "passed": report.get("passed", 0),
        "failed": report.get("failed", 0),
        "skipped": report.get("skipped", 0),
    }
