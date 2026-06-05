"""Dify 对话 inputs 组装：统一处理 user_role 等应用级变量。"""
from utils.SmartConfig import SmartConfig
from utils.logger import log

# 与 Dify「开始」节点 user_role 下拉选项严格一致（必填、无默认值）
DIFY_USER_ROLES = ("船员", "总工", "船长")


def resolve_user_role(case_data: dict) -> str:
    """
    解析用例中的 user_role，供 Dify /chat-messages 的 inputs 使用。

    - YAML 未写或为空：回落到 DEFAULT_USER_ROLE（默认 船长，常规回归高权限基线）
    - YAML 显式写明 船员 / 总工 / 船长：原样下发；越权用例通常写 船员 测 RBAC
    """
    role = case_data.get("user_role")
    if role is None:
        resolved = SmartConfig.DEFAULT_USER_ROLE
    elif isinstance(role, str) and not role.strip():
        resolved = SmartConfig.DEFAULT_USER_ROLE
    else:
        resolved = str(role).strip()

    if resolved not in DIFY_USER_ROLES:
        log.warning(
            f"user_role='{resolved}' 不在 Dify 合法枚举 {DIFY_USER_ROLES} 内，"
            f"可能触发 400 invalid_param"
        )
    return resolved


def build_dify_inputs(case_data: dict) -> dict:
    """构造 Dify payload.inputs 字典。"""
    return {"user_role": resolve_user_role(case_data)}


def is_default_role(case_data: dict) -> bool:
    """当前用例是否未显式指定角色（走了 DEFAULT_USER_ROLE）。"""
    role = case_data.get("user_role")
    return role is None or (isinstance(role, str) and not role.strip())
