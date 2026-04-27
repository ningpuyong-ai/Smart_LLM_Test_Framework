import pytest
import os
from utils.data_loader import load_yaml_data
from utils.logger import log

# 定位并加载我们刚才写的 agent_routing.yml
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AGENT_CASES = load_yaml_data("data/agent_routing.yml")

case_ids = [
    f"{case.get('case_id')}_mock:{case.get('mock_file')}"
    for case in AGENT_CASES
]


@pytest.mark.parametrize("case_data", AGENT_CASES, ids=case_ids)
def test_agent_dynamic_routing(case_data, llm_client, llm_judge, wiremock_client):
    """
    工业级 Agent 工具路由与条件拦截测试
    核心逻辑：动态注入 Mock 数据 -> 触发大模型决断 -> LLMJudge 审计决断结果
    """
    prompt_text = case_data.get("prompt")
    mock_file = case_data.get("mock_file")
    expected_behavior = case_data.get("expected_behavior")
    expected_type = case_data.get("expected_type", "tool_calling")
    user_role = case_data.get("user_role", "")

    if not mock_file:
        pytest.skip("该用例没有配置 mock_file，跳过仿真测试")

    # 1. 伴生注入 (Mock-as-Code)：把 JSON 数据打入 Docker 里的 WireMock
    mock_path = os.path.join(BASE_DIR, "data", "mocks", mock_file)
    log.info(f"===> 正在向 WireMock 注入状态仿真文件: {mock_file}")
    wiremock_client.inject_mock(mock_path)

    # 2. 触发 Agent：带上 user_role 变量发给 Dify
    test_message = [{"role": "user", "content": prompt_text}]
    inputs_var = {"user_role": user_role} if user_role else {}

    log.info(f"===> 发送 Agent 指令: '{prompt_text}', 环境变量: {inputs_var}")
    response = llm_client.send_request(test_message, inputs=inputs_var)

    assert response != "", "大模型接口返回值为空"
    if str(response).startswith("请求异常:"):
        pytest.fail(f"大模型接口请求发生底层异常: {response}")

    # 3. 智能裁判审计：把预期行为告诉 LLMJudge 让它去评判
    judge_question = f"用户指令: {prompt_text}\n系统当前底层状态必须触发如下预期行为: 【{expected_behavior}】"

    judge_result = llm_judge.evaluate_answer(
        question=judge_question,
        answer=response,
        expected_type=expected_type
    )

    is_pass = judge_result.get("is_pass", False)

    error_msg = (
        f"\n [Agent 路由决断失败] ❌\n"
        f"用例场景: 注入了 {mock_file}\n"
        f"期望行为: {expected_behavior}\n"
        f"裁判拒签原因: {judge_result.get('reason')}\n"
        f"--------------------------------------------------\n"
        f" [被测Agent真实回答]: \n{response}\n"
        f"--------------------------------------------------"
    )

    assert is_pass is True, error_msg
    log.info(f"✅ Agent 成功处理了 {mock_file} 带来的边界状态！")