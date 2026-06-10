"""Matplotlib 中文字体：按字体文件路径加载，避免 rcParams 在 Streamlit 中失效。"""
from __future__ import annotations

import os
import platform
from functools import lru_cache

from matplotlib.font_manager import FontProperties


def _fonts_dir() -> str:
    if platform.system() == "Windows":
        return os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    if platform.system() == "Darwin":
        return "/System/Library/Fonts"
    return "/usr/share/fonts"


@lru_cache(maxsize=1)
def get_cjk_font_path() -> str | None:
    """返回首个可用的中文字体文件绝对路径。"""
    font_dir = _fonts_dir()
    candidates = [
        os.path.join(font_dir, name)
        for name in (
            "msyh.ttc",
            "msyhbd.ttc",
            "simhei.ttf",
            "simsun.ttc",
            "PingFang.ttc",
            "NotoSansCJK-Regular.ttc",
            "NotoSansSC-Regular.otf",
            "wqy-microhei.ttc",
        )
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


@lru_cache(maxsize=1)
def get_cjk_fontproperties() -> FontProperties:
    """返回可用于 chart 文本的中文字体 FontProperties。"""
    path = get_cjk_font_path()
    if path:
        return FontProperties(fname=path)
    return FontProperties()


def configure_matplotlib_cjk() -> None:
    """同步设置 rcParams（辅助），图表仍应显式传入 fontproperties。"""
    from matplotlib import font_manager
    import matplotlib.pyplot as plt

    path = get_cjk_font_path()
    if not path:
        plt.rcParams["axes.unicode_minus"] = False
        return

    try:
        font_manager.fontManager.addfont(path)
    except Exception:
        pass

    family = get_cjk_fontproperties().get_name()
    plt.rcParams["font.sans-serif"] = [family, "Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False
