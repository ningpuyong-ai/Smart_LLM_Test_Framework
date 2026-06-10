"""报告数据分析：KPI、分布区间、DataFrame 转换。"""
from __future__ import annotations

from functools import lru_cache
from typing import Any

import pandas as pd

# 10 种 expected_type → 4 大工业可信维度
TRUST_DIMENSION_ORDER = (
    "事实与幻觉",
    "安全与权限管控",
    "指令遵循与意图理解",
    "基础认知与表达",
)

TRUST_DIMENSION_TYPES: dict[str, frozenset[str]] = {
    "事实与幻觉": frozenset({"factuality", "rag_closed_book", "rag_grounding"}),
    "安全与权限管控": frozenset({"security", "rbac_escalation"}),
    "指令遵循与意图理解": frozenset({"tool_calling", "roleplay"}),
    "基础认知与表达": frozenset({"general", "definition", "classification"}),
}

TYPE_TO_TRUST_DIMENSION: dict[str, str] = {
    expected_type: dimension
    for dimension, types in TRUST_DIMENSION_TYPES.items()
    for expected_type in types
}

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
                "case_id", "test_module", "expected_type", "mock_file",
                "prompt", "response", "score", "is_pass", "reason", "status",
            ]
        )
    df = pd.DataFrame(cases)
    if "expected_type" not in df.columns:
        df["expected_type"] = df.apply(
            lambda row: resolve_expected_type(row.to_dict()),
            axis=1,
        )
    return df


@lru_cache(maxsize=1)
def _case_type_lookup() -> dict[str, str]:
    """从 data/ 用例 YAML 构建 case_id → expected_type 索引，供历史报告回填。"""
    try:
        from utils.data_loader import load_yaml_data

        root = __import__("os").path.dirname(
            __import__("os").path.dirname(__import__("os").path.abspath(__file__))
        )
        cases = load_yaml_data(__import__("os").path.join(root, "data"))
        return {
            case["case_id"]: case.get("expected_type", "general")
            for case in cases
            if case.get("case_id")
        }
    except Exception:
        return {}


def resolve_expected_type(case: dict[str, Any]) -> str:
    """解析单条用例的 expected_type（报告字段优先，YAML 索引兜底）。"""
    explicit = case.get("expected_type")
    if explicit:
        return str(explicit)

    case_id = case.get("case_id", "")
    from_yaml = _case_type_lookup().get(case_id)
    if from_yaml:
        return from_yaml

    if case.get("test_module") == "test_agent_routing":
        return "tool_calling"

    return "general"


def trust_dimension_pass_rates(df: pd.DataFrame) -> pd.DataFrame:
    """
    按 4 大工业可信维度聚合通过率。
    通过率 = 维度内 PASS / (PASS + FAIL)，SKIP 不计入分母。
    """
    buckets: dict[str, dict[str, int]] = {
        dimension: {"passed": 0, "failed": 0, "skipped": 0, "total": 0}
        for dimension in TRUST_DIMENSION_ORDER
    }

    if df.empty:
        return _empty_trust_dimension_df()

    for _, row in df.iterrows():
        expected_type = resolve_expected_type(row.to_dict())
        dimension = TYPE_TO_TRUST_DIMENSION.get(expected_type)
        if dimension is None:
            continue

        bucket = buckets[dimension]
        bucket["total"] += 1
        status = row.get("status", "")
        if status == "PASS":
            bucket["passed"] += 1
        elif status == "FAIL":
            bucket["failed"] += 1
        elif status == "SKIP":
            bucket["skipped"] += 1

    rows = []
    for dimension in TRUST_DIMENSION_ORDER:
        bucket = buckets[dimension]
        evaluated = bucket["passed"] + bucket["failed"]
        pass_rate = round(bucket["passed"] / evaluated, 4) if evaluated else None
        rows.append(
            {
                "维度": dimension,
                "通过率": pass_rate,
                "通过率_pct": round(pass_rate * 100, 1) if pass_rate is not None else None,
                "用例数": bucket["total"],
                "通过数": bucket["passed"],
                "失败数": bucket["failed"],
                "跳过数": bucket["skipped"],
            }
        )
    return pd.DataFrame(rows)


def _empty_trust_dimension_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "维度": list(TRUST_DIMENSION_ORDER),
            "通过率": [None] * len(TRUST_DIMENSION_ORDER),
            "通过率_pct": [None] * len(TRUST_DIMENSION_ORDER),
            "用例数": [0] * len(TRUST_DIMENSION_ORDER),
            "通过数": [0] * len(TRUST_DIMENSION_ORDER),
            "失败数": [0] * len(TRUST_DIMENSION_ORDER),
            "跳过数": [0] * len(TRUST_DIMENSION_ORDER),
        }
    )


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
