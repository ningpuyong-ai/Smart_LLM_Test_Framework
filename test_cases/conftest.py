import pytest
from core.requests_client import get_llm_client
from evaluators.llm_judge import LLMJudge
from core.wiremock_client import WireMockClient
from utils.logger import log
from utils.report_collector import ReportCollector, install_patches


@pytest.fixture(scope="session")
def llm_client():
    log.info("\n[全局配置] 初始化 LLMClient 发包器...")
    return get_llm_client()


@pytest.fixture(scope="session")
def llm_judge():
    log.info("\n[全局配置] 初始化 LLMJudge 智能裁判...")
    return LLMJudge()


@pytest.fixture(scope="session")
def wiremock_client():
    log.info("\n[全局配置] 初始化 WireMockClient 仿真引擎...")
    client = WireMockClient()
    return client


@pytest.fixture(scope="session", autouse=True)
def _report_collection_hooks(llm_client, llm_judge):
    """旁路采集：包装客户端与裁判，会话结束时落盘 JSON 报告。"""
    ReportCollector.start_session()
    install_patches(llm_client, llm_judge)
    yield
    report_path = ReportCollector.write_report()
    if report_path:
        log.info(f"\n[评测报告] 结构化 JSON 已生成 -> {report_path}")


@pytest.fixture(autouse=True)
def _report_case_context(request):
    """每条用例执行前登记 case_data（比 pytest_runtest_setup 更稳定，覆盖 agent_routing 等场景）。"""
    callspec = getattr(request.node, "callspec", None)
    if callspec is None:
        yield
        return
    case_data = callspec.params.get("case_data")
    if case_data:
        ReportCollector.ensure_case(request.node.nodeid, case_data)
    yield


@pytest.fixture(autouse=True)
def auto_reset_mock(wiremock_client):
    """【大厂神技】：每个用例跑之前和跑之后，强制清空靶场，保证绝对不污染！"""
    wiremock_client.reset_all()
    yield
    wiremock_client.reset_all()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when != "call":
        return
    callspec = getattr(item, "callspec", None)
    if callspec is not None:
        case_data = callspec.params.get("case_data")
        if case_data:
            ReportCollector.ensure_case(item.nodeid, case_data)
    ReportCollector.set_current_nodeid(item.nodeid)
    ReportCollector.finalize_case(item.nodeid, rep.outcome)
