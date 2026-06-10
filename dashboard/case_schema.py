"""Excel 用例导入：字段定义与枚举常量。"""

ROOT_DIR = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))
TEMPLATES_DIR = __import__("os").path.join(ROOT_DIR, "templates")
TEMPLATE_FILENAME = "test_cases_template.xlsx"
TEMPLATE_PATH = __import__("os").path.join(TEMPLATES_DIR, TEMPLATE_FILENAME)
IMPORTED_YAML_PATH = __import__("os").path.join(ROOT_DIR, "data", "imported_excel_cases.yml")

# 模板列顺序（严格）
TEMPLATE_COLUMNS = [
    "case_id",
    "expected_type",
    "prompt",
    "user_role",
    "mock_file",
]

REQUIRED_COLUMNS = frozenset({"case_id", "expected_type", "prompt"})
OPTIONAL_COLUMNS = frozenset({"user_role", "mock_file"})

EXPECTED_TYPES = (
    "general",
    "security",
    "factuality",
    "definition",
    "classification",
    "roleplay",
    "rag_closed_book",
    "rag_grounding",
    "tool_calling",
    "rbac_escalation",
)

USER_ROLES = ("船长", "总工", "船员")

EXPECTED_TYPE_LABELS = {
    "general": "通用问答",
    "security": "安全防御",
    "factuality": "事实性/反幻觉",
    "definition": "概念解释",
    "classification": "分类列举",
    "roleplay": "角色扮演",
    "rag_closed_book": "RAG 闭卷",
    "rag_grounding": "RAG 落地召回",
    "tool_calling": "工具调用/路由",
    "rbac_escalation": "RBAC 越权",
}
