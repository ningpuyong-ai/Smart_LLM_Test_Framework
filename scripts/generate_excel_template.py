"""脚手架：生成标准 Excel 用例模板。运行: python scripts/generate_excel_template.py"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dashboard.excel_export import generate_excel_template
from dashboard.case_schema import TEMPLATE_PATH


if __name__ == "__main__":
    path = generate_excel_template(TEMPLATE_PATH)
    print(f"模板已生成: {path}")
