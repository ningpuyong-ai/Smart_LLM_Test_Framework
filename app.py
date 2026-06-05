"""
Smart LLM 评测监控大盘 — Streamlit 入口
运行: streamlit run app.py
"""
import streamlit as st

from dashboard.analytics import (
    cases_to_dataframe,
    failed_cases,
    kpi_from_report,
    score_distribution,
    status_distribution,
)
from dashboard.report_io import REPORTS_DIR, list_report_files, load_report, report_label
from dashboard.ui_components import (
    render_detail_table,
    render_failed_probe,
    render_kpi_row,
    render_score_distribution,
    render_status_pie,
)

st.set_page_config(
    page_title="Smart LLM 评测监控大盘",
    page_icon="📊",
    layout="wide",
)

st.title("Smart LLM 评测监控大盘")
st.caption("读取 `reports/` 目录下的 pytest 结构化 JSON 报告，进行多轮历史对比分析。")

report_files = list_report_files()

with st.sidebar:
    st.header("历史评测任务")
    st.caption(f"报告目录: `{REPORTS_DIR}`")

    if not report_files:
        st.warning("暂无报告文件。请先运行 `pytest` 生成 JSON 报告。")
        st.stop()

    labels = []
    file_by_label = {}
    for fname in report_files:
        data = load_report(fname)
        if data is None:
            continue
        label = report_label(fname, data)
        labels.append(label)
        file_by_label[label] = fname

    selected_label = st.selectbox("选择评测任务", labels, index=0)
    selected_file = file_by_label[selected_label]

report = load_report(selected_file)
if not report:
    st.error("报告文件读取失败，请检查 JSON 格式。")
    st.stop()

st.info(
    f"当前查看报告：**{report.get('run_id', selected_file)}** "
    f"（{report.get('start_time', '')} ~ {report.get('end_time', '')}）。"
    f"若与终端 pytest 不一致，请确认侧边栏选的是**最新一次**运行生成的 JSON，或重新执行 `pytest` 后再刷新页面。"
)

df = cases_to_dataframe(report)
kpi = kpi_from_report(report, df)

render_kpi_row(kpi)

st.divider()

chart_left, chart_right = st.columns(2)
with chart_left:
    render_score_distribution(score_distribution(df))
with chart_right:
    render_status_pie(status_distribution(df))

st.divider()

with st.expander("失败用例探针（业务复盘）", expanded=bool(len(failed_cases(df)))):
    render_failed_probe(failed_cases(df))

st.divider()
render_detail_table(df)

with st.expander("运行元数据"):
    st.json(
        {
            "run_id": report.get("run_id"),
            "start_time": report.get("start_time"),
            "end_time": report.get("end_time"),
            "total_cases": report.get("total_cases"),
            "passed": report.get("passed"),
            "failed": report.get("failed"),
            "skipped": report.get("skipped"),
            "pass_rate": report.get("pass_rate"),
        }
    )
