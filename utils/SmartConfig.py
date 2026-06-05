import os
from dotenv import load_dotenv

load_dotenv()

class SmartConfig:
    """全局配置加载器：集中管理所有的环境变量和配置参数"""

    # ===== 核心：当前激活的测试平台 (dify 或 openai) =====
    # 如果配置为 dify，走 Dify 的 Agent 接口
    # 如果配置为 openai，走兼容 OpenAI 标准的接口 (包含 Ollama 裸模型)
    API_PLATFORM = os.getenv("API_PLATFORM", "dify").lower()

    # 1. 被测大模型基础配置 (支持 Dify 或 直接连模型)
    LLM_API_KEY = os.getenv("LLM_API_KEY", "默认key")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "qwen:latest")

    # 2. 裁判大模型配置（解耦核心：如果没配置，就降级使用被测模型）
    # 裁判严格绑定在 OpenAI 标准上，因为我们要直接调用它打分，不需要经过 Dify
    JUDGE_API_KEY = os.getenv("JUDGE_API_KEY") or LLM_API_KEY
    JUDGE_BASE_URL = os.getenv("JUDGE_BASE_URL") or LLM_BASE_URL
    JUDGE_MODEL = os.getenv("JUDGE_MODEL") or DEFAULT_MODEL

    # 3. Dify 应用级变量：合法值仅 船员 | 总工 | 船长（必填、无默认值）
    # 常规回归默认 船长（高权限）；越权/RBAC 用例请在 YAML 显式写 user_role: 船员
    DEFAULT_USER_ROLE = os.getenv("DEFAULT_USER_ROLE", "船长")

    @classmethod
    def get_timeout(cls):
        """动态获取超时时间"""
        timeout_str = os.getenv("REQUEST_TIMEOUT", "30")
        try:
            return int(timeout_str)
        except (ValueError, TypeError):
            return 30

    @classmethod
    def get_headers(cls, is_judge=False):
        """获取大模型请求的标准请求头"""
        api_key = cls.JUDGE_API_KEY if is_judge else cls.LLM_API_KEY
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }