"""Streamlit UI 组件：与数据处理解耦的纯渲染函数。"""
import matplotlib

matplotlib.use("Agg")

import pandas as pd
import streamlit as st

from dashboard.chart_fonts import configure_matplotlib_cjk, get_cjk_fontproperties

configure_matplotlib_cjk()


def render_kpi_row(kpi: dict) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总用例数", kpi["total_cases"])
    c2.metric("通过率", f"{kpi['pass_rate_pct']}%")
    c3.metric("平均分", kpi["avg_score"])
    c4.metric("通过 / 失败 / 跳过", f"{kpi['passed']} / {kpi['failed']} / {kpi['skipped']}")


def render_trust_dimension_dashboard(trust_df: pd.DataFrame) -> None:
    """工业可信四维 KPI 看板 + 通过率柱状图 / 雷达图。"""
    st.subheader("工业可信维度")
    st.caption(
        "将 10 种 expected_type 聚合为 4 大核心维度，"
        "通过率 = 维度内 PASS / (PASS + FAIL)。"
    )

    cols = st.columns(4)
    for col, (_, row) in zip(cols, trust_df.iterrows()):
        pct = row["通过率_pct"]
        if pct is None or row["用例数"] == 0:
            col.metric(
                row["维度"],
                "—",
                help="当前维度暂无有效评测用例",
            )
            continue
        col.metric(
            row["维度"],
            f"{pct}%",
            f"{row['通过数']}/{row['通过数'] + row['失败数']} 通过",
        )

    chart_left, chart_right = st.columns(2)
    with chart_left:
        _render_trust_dimension_bar(trust_df)
    with chart_right:
        _render_trust_dimension_radar(trust_df)


def _render_trust_dimension_bar(trust_df: pd.DataFrame) -> None:
    st.markdown("##### 维度通过率（柱状图）")
    plot_df = trust_df.dropna(subset=["通过率_pct"])
    if plot_df.empty:
        st.info("暂无维度通过率数据。")
        return

    chart_df = plot_df.set_index("维度")[["通过率_pct"]].rename(columns={"通过率_pct": "通过率 (%)"})
    st.bar_chart(chart_df, height=360, use_container_width=True)


def _render_trust_dimension_radar(trust_df: pd.DataFrame) -> None:
    st.markdown("##### 维度通过率（雷达图）")
    plot_df = trust_df.dropna(subset=["通过率_pct"])
    if plot_df.empty:
        st.info("暂无维度通过率数据。")
        return

    import matplotlib.pyplot as plt
    import numpy as np

    fp = get_cjk_fontproperties()
    labels = plot_df["维度"].tolist()
    values = plot_df["通过率_pct"].tolist()
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values_closed = values + [values[0]]
    angles_closed = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(5.5, 4.5), subplot_kw={"polar": True})
    ax.plot(angles_closed, values_closed, color="#3498db", linewidth=2)
    ax.fill(angles_closed, values_closed, color="#3498db", alpha=0.25)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, fontproperties=fp, fontsize=8)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], fontsize=7)
    ax.set_title("四维通过率雷达", fontproperties=fp, fontsize=10, pad=20)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def render_score_distribution(dist_df: pd.DataFrame) -> None:
    st.subheader("得分分布")
    if dist_df.empty or dist_df["数量"].sum() == 0:
        st.info("当前任务暂无有效分数数据。")
        return
    import matplotlib.pyplot as plt

    fp = get_cjk_fontproperties()
    fig, ax = plt.subplots(figsize=(6, 4))
    x_pos = range(len(dist_df))
    ax.bar(x_pos, dist_df["数量"], color="#3498db")
    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(dist_df["区间"], fontproperties=fp, rotation=30, ha="right")
    ax.set_xlabel("得分区间", fontproperties=fp)
    ax.set_ylabel("用例数", fontproperties=fp)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def render_status_pie(status_df: pd.DataFrame) -> None:
    st.subheader("用例状态占比")
    if status_df.empty:
        st.info("暂无状态统计数据。")
        return
    st.pyplot(_build_pie_chart(status_df))


def _build_pie_chart(status_df: pd.DataFrame):
    import matplotlib.pyplot as plt

    configure_matplotlib_cjk()
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
