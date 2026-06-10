"""用例管理与导入 Tab 渲染。"""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

from dashboard.case_schema import EXPECTED_TYPE_LABELS, IMPORTED_YAML_PATH, TEMPLATE_FILENAME
from dashboard.excel_export import count_nonempty_column, ensure_template_exists, save_cases_to_yaml
from dashboard.excel_validator import validate_excel_upload


def render_case_import_tab() -> None:
    st.subheader("用例管理与导入")
    st.caption(
        "下载标准 Excel 模板 → 填写用例 → 上传校验 → 确认后生成 "
        f"`data/imported_excel_cases.yml`，供 `pytest` 单轮评测自动加载。"
    )

    template_path = ensure_template_exists()

    st.markdown("#### 1. 下载模板")
    with open(template_path, "rb") as f:
        st.download_button(
            label="📥 下载 Excel 用例模板",
            data=f.read(),
            file_name=TEMPLATE_FILENAME,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
        )

    with st.expander("字段与用例类型说明"):
        st.markdown(
            "| 列名 | 必填 | 说明 |\n|------|------|------|\n"
            "| case_id | ✅ | 用例唯一 ID |\n"
            "| expected_type | ✅ | 用例类型（模板内下拉） |\n"
            "| prompt | ✅ | 提示词 |\n"
            "| user_role | ❌ | 船长 / 总工 / 船员 |\n"
            "| mock_file | ❌ | Agent 路由 Mock 文件名 |"
        )
        type_rows = [
            f"| `{k}` | {v} |" for k, v in EXPECTED_TYPE_LABELS.items()
        ]
        st.markdown("**expected_type 枚举：**\n\n" + "\n".join(type_rows))

    st.divider()
    st.markdown("#### 2. 上传并校验")

    uploaded = st.file_uploader(
        "上传已填写的 Excel（.xlsx）",
        type=["xlsx"],
        help="请使用标准模板填写，勿改列名与列顺序。",
    )

    if uploaded is None:
        if os.path.isfile(IMPORTED_YAML_PATH):
            st.info(f"当前已存在导入文件: `{IMPORTED_YAML_PATH}`，重新导入将覆盖。")
        return

    try:
        raw_df = pd.read_excel(uploaded, sheet_name="用例列表", engine="openpyxl")
    except Exception:
        try:
            raw_df = pd.read_excel(uploaded, sheet_name=0, engine="openpyxl")
        except Exception as exc:
            st.error(f"Excel 读取失败: {exc}")
            return

    ok, valid_df, errors = validate_excel_upload(raw_df)

    if not ok:
        st.error(f"校验未通过，共 {len(errors)} 个问题：")
        for err in errors:
            st.markdown(f"- :red[{err}]")
        if valid_df is not None:
            st.markdown("##### 已解析数据预览（供排查）")
            st.dataframe(valid_df, use_container_width=True, hide_index=True)
        return

    st.success(f"✅ 校验通过！共 {len(valid_df)} 条用例，可预览并落盘。")
    st.dataframe(valid_df, use_container_width=True, hide_index=True)

    mock_count = count_nonempty_column(valid_df, "mock_file")
    if mock_count:
        st.warning(
            f"其中 {mock_count} 条含 `mock_file`：单轮评测会自动跳过；"
            "若需 WireMock 路由测试，请同步维护 `data/agent_routing.yml`。"
        )

    st.divider()
    st.markdown("#### 3. 确认落盘")

    if st.button("确认并生成 YAML 用例", type="primary"):
        try:
            out_path = save_cases_to_yaml(valid_df)
            st.success(f"已生成 YAML: `{out_path}`")
            st.code(out_path, language="text")
            st.info("执行 `pytest test_cases/test_single_turn.py` 即可加载（不含 mock_file 条目）。")
        except Exception as exc:
            st.error(f"YAML 写入失败: {exc}")
