import requests
import json


class WireMockClient:
    def __init__(self, base_url="http://localhost:8081"):
        self.admin_url = f"{base_url}/__admin/mappings"
        self.reset_url = f"{base_url}/__admin/mappings/reset"

    def inject_mock(self, json_file_path):
        """读取本地 JSON 资产文件，动态注入到 WireMock"""
        with open(json_file_path, 'r', encoding='utf-8') as f:
            mock_data = json.load(f)

        response = requests.post(self.admin_url, json=mock_data)
        if response.status_code != 201:
            raise Exception(f"❌ Mock 注入失败! 状态码: {response.status_code}, 报错: {response.text}")
        return True

    def reset_all(self):
        """一键清空所有动态 Mock 数据，保证测试环境纯净"""
        requests.post(self.reset_url)