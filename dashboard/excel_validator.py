"""Excel 用例极严校验与 DataFrame 规范化。"""
from __future__ import annotations

import pandas as pd

from dashboard.case_schema import (
    EXPECTED_TYPES,
    OPTIONAL_COLUMNS,
    REQUIRED_COLUMNS,
    TEMPLATE_COLUMNS,
    USER_ROLES,
)


def _excel_row_number(df_index: int) -> int:
    """DataFrame 行号（0-based）对应 Excel 行号（含表头）。"""
    return df_index + 2


def is_empty_cell_value(value) -> bool:
    """判断单元格是否为空（None / NaN / pd.NA / 空串 / 字符串 nan / .nan）。"""
    if value is None:
        return True
    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass
    if isinstance(value, float):
        import math
        if math.isnan(value):
            return True
    text = str(value).strip()
    return text == "" or text.lower() in ("nan", ".nan")


def _is_empty(value) -> bool:
    return is_empty_cell_value(value)


def _normalize_cell(value, *, optional: bool = False) -> str:
    if _is_empty(value):
        return "" if optional else ""
    return str(value).strip()


def normalize_uploaded_dataframe(raw_df: pd.DataFrame) -> tuple[pd.DataFrame | None, list[str]]:
    """列名对齐、去空格、合并单元格 NaN 置空。"""
    errors: list[str] = []

    if raw_df is None or raw_df.empty:
        return None, ["Excel 为空或没有可读取的数据行。"]

    df = raw_df.copy()
    df.columns = [str(col).strip() for col in df.columns]

    missing = [col for col in TEMPLATE_COLUMNS if col not in df.columns]
    extra = [col for col in df.columns if col not in TEMPLATE_COLUMNS]
    if missing:
        errors.append(f"缺少必填列: {', '.join(missing)}")
    if extra:
        errors.append(f"存在未定义的多余列（请删除）: {', '.join(extra)}")
    if errors:
        return None, errors

    df = df[TEMPLATE_COLUMNS].copy()

    # 删除整行空白（合并单元格常见）
    def _row_all_blank(row) -> bool:
        return all(_is_empty(row[col]) for col in TEMPLATE_COLUMNS)

    blank_mask = df.apply(_row_all_blank, axis=1)
    if blank_mask.all():
        return None, ["所有数据行均为空，请填写用例后再上传。"]
    df = df.loc[~blank_mask].reset_index(drop=True)

    for col in TEMPLATE_COLUMNS:
        optional = col in OPTIONAL_COLUMNS
        df[col] = df[col].apply(lambda v, opt=optional: _normalize_cell(v, optional=opt))

    # 可选列统一为 object + 空串，避免 StringDtype 把 None 显示/回写为 nan
    for col in OPTIONAL_COLUMNS:
        df[col] = df[col].apply(lambda v: "" if is_empty_cell_value(v) else str(v).strip())
        df[col] = df[col].astype(object)

    return df, []


def validate_cases_dataframe(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """返回 (是否通过, 错误列表，含 Excel 行号)。"""
    errors: list[str] = []
    seen_case_ids: dict[str, int] = {}

    for idx, row in df.iterrows():
        row_no = _excel_row_number(idx)

        for col in REQUIRED_COLUMNS:
            if _is_empty(row[col]):
                errors.append(f"第 {row_no} 行: 必填列 `{col}` 不能为空。")

        case_id = row.get("case_id")
        if not _is_empty(case_id):
            if case_id in seen_case_ids:
                errors.append(
                    f"第 {row_no} 行: case_id `{case_id}` 与第 {seen_case_ids[case_id]} 行重复。"
                )
            else:
                seen_case_ids[case_id] = row_no

        expected_type = row.get("expected_type")
        if not _is_empty(expected_type) and expected_type not in EXPECTED_TYPES:
            errors.append(
                f"第 {row_no} 行: expected_type `{expected_type}` 非法，"
                f"必须为以下之一: {', '.join(EXPECTED_TYPES)}"
            )

        user_role = row.get("user_role")
        if not _is_empty(user_role) and user_role not in USER_ROLES:
            errors.append(
                f"第 {row_no} 行: user_role `{user_role}` 非法，必须为: {', '.join(USER_ROLES)}"
            )

        prompt = row.get("prompt")
        if not _is_empty(prompt) and len(str(prompt)) < 2:
            errors.append(f"第 {row_no} 行: prompt 过短，请填写完整提示词。")

    return len(errors) == 0, errors


def validate_excel_upload(raw_df: pd.DataFrame) -> tuple[bool, pd.DataFrame | None, list[str]]:
    df, norm_errors = normalize_uploaded_dataframe(raw_df)
    if norm_errors:
        return False, None, norm_errors
    ok, val_errors = validate_cases_dataframe(df)
    if not ok:
        return False, df, val_errors
    return True, df, []
