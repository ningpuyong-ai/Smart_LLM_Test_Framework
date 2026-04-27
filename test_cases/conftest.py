import pytest
from core.requests_client import get_llm_client
from evaluators.llm_judge import LLMJudge
from core.wiremock_client import WireMockClient
from utils.logger import log

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

@pytest.fixture(autouse=True)
def auto_reset_mock(wiremock_client):
    """【大厂神技】：每个用例跑之前和跑之后，强制清空靶场，保证绝对不污染！"""
    wiremock_client.reset_all()
    yield
    wiremock_client.reset_all()