"""报告文件 IO：扫描与加载 reports/ 目录下的 JSON。"""
import json
import os
from typing import Any, Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")


def list_report_files() -> list[str]:
    if not os.path.isdir(REPORTS_DIR):
        return []
    files = [
        f for f in os.listdir(REPORTS_DIR)
        if f.endswith(".json") and f.startswith("run_")
    ]
    files.sort(reverse=True)
    return files


def load_report(file_name: str) -> Optional[dict[str, Any]]:
    path = os.path.join(REPORTS_DIR, file_name)
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def report_label(file_name: str, report: dict[str, Any]) -> str:
    run_id = report.get("run_id", file_name.replace(".json", ""))
    start = report.get("start_time", "未知时间")
    passed = report.get("passed", 0)
    total = report.get("total_cases", 0)
    return f"{run_id} | {start} | 通过 {passed}/{total}"
