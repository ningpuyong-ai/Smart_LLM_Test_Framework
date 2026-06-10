"""
Smart LLM 评测监控大盘 — Streamlit 入口
运行: streamlit run app.py
"""
import streamlit as st

from dashboard.case_import_ui import render_case_import_tab
from dashboard.dashboard_page import render_dashboard_tab

PAGE_DASHBOARD = "历史评测大盘"
PAGE_IMPORT = "用例管理与导入"

MENU_ITEMS: dict[str, callable] = {
    PAGE_DASHBOARD: render_dashboard_tab,
    PAGE_IMPORT: render_case_import_tab,
}


def inject_custom_css() -> None:
    """侧栏与面包屑样式；可按需调整颜色、字号、间距。"""
    st.markdown(
        """
        <style>
        /* ── 侧栏容器 ── */
        section[data-testid="stSidebar"] {
            background-color: #1e293b;
            border-right: 1px solid #334155;
        }
        section[data-testid="stSidebar"] > div {
            padding-top: 1.25rem;
        }

        /* ── 侧栏文字默认色 ── */
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] .stMarkdown p {
            color: #e2e8f0 !important;
        }

        /* ── 品牌区 ── */
        .erp-sidebar-brand {
            padding: 0.25rem 0.5rem 1.25rem 0.5rem;
            border-bottom: 1px solid #334155;
            margin-bottom: 1rem;
        }
        .erp-sidebar-brand .brand-title {
            color: #f8fafc;
            font-size: 1.05rem;
            font-weight: 700;
            line-height: 1.4;
            margin: 0;
        }
        .erp-sidebar-brand .brand-sub {
            color: #cbd5e1;
            font-size: 0.78rem;
            margin: 0.15rem 0 0 0;
        }

        /* ── 导航菜单（radio 伪装为纵向菜单） ── */
        section[data-testid="stSidebar"] .stRadio > div {
            flex-direction: column;
            gap: 0.35rem;
        }
        section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {
            background-color: transparent;
            border-left: 3px solid transparent;
            border-radius: 0 6px 6px 0;
            padding: 0.55rem 0.75rem;
            margin: 0;
            width: 100%;
            font-size: 0.95rem;
            font-weight: 500;
            color: #f1f5f9 !important;
            transition: background-color 0.15s ease, border-color 0.15s ease;
        }
        /* 覆盖 Streamlit radio 内部文字节点 */
        section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] p,
        section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] span,
        section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] div {
            color: #f1f5f9 !important;
        }
        section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:hover {
            background-color: rgba(148, 163, 184, 0.18);
        }
        section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked) {
            background-color: rgba(59, 130, 246, 0.35);
            border-left-color: #60a5fa;
            color: #ffffff !important;
            font-weight: 600;
        }
        section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked) p,
        section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked) span,
        section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked) div {
            color: #ffffff !important;
            font-weight: 600;
        }
        section[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] > div:first-child {
            display: none;
        }

        /* ── 主区面包屑 ── */
        .erp-breadcrumb {
            color: #64748b;
            font-size: 0.82rem;
            margin-bottom: 0.35rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid #e2e8f0;
        }
        .erp-breadcrumb .current {
            color: #334155;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(
    page_title="Smart LLM 评测监控大盘",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_css()

with st.sidebar:
    st.markdown(
        """
        <div class="erp-sidebar-brand">
            <p class="brand-title">Smart LLM 评测系统</p>
            <p class="brand-sub">工业 Agent 自动化评测</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_page = st.radio(
        "导航",
        list(MENU_ITEMS.keys()),
        label_visibility="collapsed",
        key="main_nav",
    )

st.markdown(
    f'<div class="erp-breadcrumb">首页 / <span class="current">{selected_page}</span></div>',
    unsafe_allow_html=True,
)

MENU_ITEMS[selected_page]()
