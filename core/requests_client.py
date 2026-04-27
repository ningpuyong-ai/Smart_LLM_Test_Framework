import requests
import json
import time
from typing import Union
from utils.logger import log
from utils.SmartConfig import SmartConfig

import logging
import http.client as http_client

# 开启 Python 底层 HTTP 连接的“显微镜”模式
http_client.HTTPConnection.debuglevel = 1

# 把所有隐藏的网络请求全部打印到控制台
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

class BaseLLMClient:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = SmartConfig.LLM_BASE_URL
        self.session.headers.update(SmartConfig.get_headers(is_judge=False))

    # 【新增】增加了 inputs 参数，支持 Dify 的变量注入
    def send_request(self, message: Union[list, str], model: str = None, inputs: dict = None) -> str:
        raise NotImplementedError("子类必须实现具体的发送请求方法")

class DifyClient(BaseLLMClient):
    def send_request(self, message: Union[list, str], model: str = None, inputs: dict = None) -> str:
        if not message:
            raise ValueError("错误: message入参不能为空!")

        if isinstance(message, list):
            query_text = message[-1].get("content", "")
        else:
            query_text = str(message)

        if not query_text.strip():
            raise ValueError("错误: 提取到的query_text为空，无法发送请求")

        url = f"{self.base_url}/chat-messages"
        # 【核心修复】：将外部传入的变量（如 user_role）塞进 payload
        payload = {
            "inputs": inputs or {},
            "query": query_text,
            "response_mode": "streaming",
            "user": "autotest_user"
        }

        full_response = ""
        log.info(f"开始向 Dify 发送请求 (携带变量: {payload['inputs']})...")
        start_time = time.time()

        try:
            with self.session.post(url, json=payload, stream=True, timeout=SmartConfig.get_timeout()) as resp:
                if resp.status_code >= 400:
                    error_detail = resp.text
                    log.error(f" Dify 接口打回了请求! HTTP状态码: {resp.status_code}, 真实原因: {error_detail}")
                    return f"请求异常: {resp.status_code} - {error_detail}"

                resp.raise_for_status()
                for line in resp.iter_lines(decode_unicode=True):
                    if not line:
                        continue
                    if line.startswith("data: "):
                        json_str = line[6:]
                        if json_str == "[DONE]":
                            break
                        try:
                            data_dict = json.loads(json_str)
                            # === 【核心修复】扩大撒网范围，捕获各种 Agent 事件里的碎片 ===
                            event_type = data_dict.get("event")

                            # 1. 捕获普通的对话碎片
                            if event_type == "message":
                                full_response += data_dict.get("answer", "")

                            # 2. 捕获 Agent 专属的推理结论碎片 (非常关键！)
                            elif event_type == "agent_message":
                                full_response += data_dict.get("answer", "")

                            # 3. 把 Agent 思考的过程也抓下来
                            elif event_type == "agent_thought":
                                thought = data_dict.get("thought", "")
                                tool = data_dict.get("tool", "")
                                log.info(f" [Agent 思考中] -> {thought}")
                                if tool:
                                    log.warning(f"🔧 [Agent 试图调用工具] -> 准备调用: {tool}")

                            elif event_type == "tool_response":
                                tool_output = data_dict.get("tool_output", "")
                                log.warning(f" [工具真实返回数据] -> {tool_output}")

                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            log.error(f"Dify 请求发生网络底层异常: {str(e)}")
            return f"请求异常: {str(e)}"

        end_time = time.time()
        log.info(f"Dify 响应完毕，总耗时：{int(end_time - start_time)}秒")
        return full_response

class OpenAIClient(BaseLLMClient):
    def send_request(self, message: Union[list, str], model: str = None, inputs: dict = None) -> str:
        # OpenAI 标准暂不需要特殊处理 inputs，保持原样
        if not message:
            raise ValueError("错误: message入参不能为空!")

        if isinstance(message, str):
            messages = [{"role": "user", "content": message}]
        else:
            messages = message

        model_name = model or SmartConfig.DEFAULT_MODEL
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False
        }

        log.info(f"开始向 OpenAI 标准接口请求模型 {model_name}...")
        start_time = time.time()

        try:
            response = self.session.post(url, json=payload, timeout=SmartConfig.get_timeout())
            response.raise_for_status()
            result_json = response.json()
            full_response = result_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            log.error(f"OpenAI标准接口请求发生异常: {str(e)}")
            return f"请求异常: {str(e)}"

        end_time = time.time()
        log.info(f"模型响应完毕，总耗时：{int(end_time - start_time)}秒")
        return full_response

def get_llm_client():
    platform = SmartConfig.API_PLATFORM
    if platform == "dify":
        return DifyClient()
    elif platform == "openai":
        return OpenAIClient()
    else:
        raise ValueError(f"不支持的 API_PLATFORM 配置: {platform}")

LLMClient = None