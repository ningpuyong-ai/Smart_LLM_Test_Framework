"""Streamlit UI 组件：与数据处理解耦的纯渲染函数。"""
import matplotlib

matplotlib.use("Agg")

import pandas as pd
import streamlit as st


def render_kpi_row(kpi: dict) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总用例数", kpi["total_cases"])
    c2.metric("通过率", f"{kpi['pass_rate_pct']}%")
    c3.metric("平均分", kpi["avg_score"])
    c4.metric("通过 / 失败 / 跳过", f"{kpi['passed']} / {kpi['failed']} / {kpi['skipped']}")


def render_score_distribution(dist_df: pd.DataFrame) -> None:
    st.subheader("得分分布")
    if dist_df.empty or dist_df["数量"].sum() == 0:
        st.info("当前任务暂无有效分数数据。")
        return
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(dist_df["区间"], dist_df["数量"], color="#3498db")
    ax.set_xlabel("得分区间")
    ax.set_ylabel("用例数")
    plt.xticks(rotation=30, ha="right")
    fig.tight_layout()
    st.pyplot(fig)


def render_status_pie(status_df: pd.DataFrame) -> None:
    st.subheader("用例状态占比")
    if status_df.empty:
        st.info("暂无状态统计数据。")
        return
    st.pyplot(_build_pie_chart(status_df))


def _build_pie_chart(status_df: pd.DataFrame):
    import matplotlib.pyplot as plt

    color_map = {
        "PASS": "#2ecc71",
        "FAIL": "#e74c3c",
        "SKIP": "#95a5a6",
        "PENDING": "#bdc3c7",
    }
    colors = [color_map.get(s, "#3498db") for s in status_df["状态"]]

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.pie(
        status_df["数量"],
        labels=status_df["状态"],
        autopct="%1.1f%%",
        startangle=90,
        colors=colors,
    )
    ax.axis("equal")
    fig.tight_layout()
    return fig


def render_failed_probe(failed_df: pd.DataFrame) -> None:
    st.subheader("失败用例专属探针")
    if failed_df.empty:
        st.success("本次评测无失败用例。")
        return

    for _, row in failed_df.iterrows():
        mock_tag = f" | mock:{row['mock_file']}" if row.get("mock_file") else ""
        module_tag = row.get("test_module") or "unknown"
        title = f"FAIL | {row.get('case_id', 'unknown')} | {module_tag}{mock_tag}"
        with st.expander(title, expanded=True):
            left, right = st.columns(2)
            with left:
                st.markdown("**被测模型真实回答**")
                st.error(row.get("response") or "（无回答记录）")
            with right:
                st.markdown("**裁判判定不合格原因**")
                st.warning(row.get("reason") or "（未记录原因）")
            st.caption(f"题目摘要：{str(row.get('prompt', ''))[:120]}...")


def render_detail_table(df: pd.DataFrame) -> None:
    st.subheader("原始数据明细")
    st.dataframe(df, use_container_width=True, hide_index=True)
