"""
评测报告旁路采集器：在不改动测试断言的前提下，收集用例执行数据并落盘 JSON。
"""
import json
import os
from datetime import datetime
from typing import Any, Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")

SECURITY_RULE_PASS_REASON = "规则短路：命中安全拒答关键词，未调用 LLM 裁判"


class ReportCollector:
    """进程内单会话采集器，与一次 pytest 运行生命周期对齐。"""

    _session_meta: Optional[dict] = None
    _cases: dict[str, dict] = {}
    _current_nodeid: Optional[str] = None

    @classmethod
    def start_session(cls) -> None:
        run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")
        cls._session_meta = {
            "run_id": run_id,
            "start_time": datetime.now().isoformat(timespec="seconds"),
            "end_time": None,
            "total_cases": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "pass_rate": 0.0,
        }
        cls._cases = {}
        cls._current_nodeid = None

    @classmethod
    def set_current_nodeid(cls, nodeid: str) -> None:
        cls._current_nodeid = nodeid

    @classmethod
    def begin_case(cls, nodeid: str, case_data: dict) -> None:
        cls._current_nodeid = nodeid
        test_module = nodeid.split("::")[0].rsplit("/", 1)[-1].replace(".py", "")
        cls._cases[nodeid] = {
            "nodeid": nodeid,
            "test_module": test_module,
            "case_id": case_data.get("case_id", "unknown"),
            "prompt": case_data.get("prompt", "") or "",
            "expected_type": case_data.get("expected_type", "general"),
            "mock_file": case_data.get("mock_file") or "",
            "response": "",
            "score": None,
            "is_pass": None,
            "reason": "",
            "status": "PENDING",
        }

    @classmethod
    def ensure_case(cls, nodeid: str, case_data: dict) -> None:
        if nodeid not in cls._cases:
            cls.begin_case(nodeid, case_data)
        else:
            cls.set_current_nodeid(nodeid)

    @classmethod
    def record_response(cls, response: str) -> None:
        case = cls._get_current_case()
        if case is not None:
            case["response"] = response or ""

    @classmethod
    def record_judge(cls, judge_result: dict) -> None:
        case = cls._get_current_case()
        if case is None:
            return
        case["score"] = judge_result.get("score")
        case["is_pass"] = judge_result.get("is_pass")
        case["reason"] = judge_result.get("reason", "") or ""

    @classmethod
    def finalize_case(cls, nodeid: str, outcome: str) -> None:
        if nodeid not in cls._cases:
            return

        status_map = {
            "passed": "PASS",
            "failed": "FAIL",
            "skipped": "SKIP",
        }
        case = cls._cases[nodeid]
        case["status"] = status_map.get(outcome, outcome.upper())

        if case["status"] == "PASS" and case["score"] is None and case["expected_type"] == "security":
            case["score"] = 100
            case["is_pass"] = True
            case["reason"] = SECURITY_RULE_PASS_REASON

        if case["status"] == "FAIL" and not case["reason"]:
            case["reason"] = "用例断言失败（可能未进入裁判或接口异常）"

    @classmethod
    def write_report(cls) -> Optional[str]:
        if cls._session_meta is None:
            return None

        cls._session_meta["end_time"] = datetime.now().isoformat(timespec="seconds")

        cases_list = list(cls._cases.values())
        passed = sum(1 for c in cases_list if c["status"] == "PASS")
        failed = sum(1 for c in cases_list if c["status"] == "FAIL")
        skipped = sum(1 for c in cases_list if c["status"] == "SKIP")
        total = len(cases_list)

        cls._session_meta["total_cases"] = total
        cls._session_meta["passed"] = passed
        cls._session_meta["failed"] = failed
        cls._session_meta["skipped"] = skipped
        cls._session_meta["pass_rate"] = round(passed / total, 4) if total else 0.0

        payload = {
            **cls._session_meta,
            "cases": [
                {
                    "case_id": c["case_id"],
                    "test_module": c.get("test_module", ""),
                    "mock_file": c.get("mock_file", ""),
                    "prompt": c["prompt"],
                    "response": c["response"],
                    "score": c["score"],
                    "is_pass": c["is_pass"],
                    "reason": c["reason"],
                    "status": c["status"],
                }
                for c in cases_list
            ],
        }

        os.makedirs(REPORTS_DIR, exist_ok=True)
        file_name = f"{cls._session_meta['run_id']}.json"
        file_path = os.path.join(REPORTS_DIR, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return file_path

    @classmethod
    def _get_current_case(cls) -> Optional[dict]:
        if cls._current_nodeid and cls._current_nodeid in cls._cases:
            return cls._cases[cls._current_nodeid]
        return None


def install_patches(llm_client: Any, llm_judge: Any) -> None:
    """包装发包器与裁判，旁路记录 response / judge 结果。"""

    original_send = llm_client.send_request

    def wrapped_send(message, model=None, inputs=None):
        response = original_send(message, model=model, inputs=inputs)
        ReportCollector.record_response(response)
        return response

    llm_client.send_request = wrapped_send

    original_evaluate = llm_judge.evaluate_answer

    def wrapped_evaluate(question: str, answer: str, expected_type: str = "general"):
        result = original_evaluate(question, answer, expected_type)
        ReportCollector.record_judge(result)
        return result

    llm_judge.evaluate_answer = wrapped_evaluate
