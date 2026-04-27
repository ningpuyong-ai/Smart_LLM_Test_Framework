import datetime
import os
import logging
import colorlog


def setup_logger():
    """
    配置全局日志：终端带颜色输出 + 文件永久留存
    """
    logger = logging.getLogger("SmartLLM_Framework")

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # ================= 1. 终端输出配置 (带颜色) =================
        log_colors_config = {
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
        console_formatter = colorlog.ColoredFormatter(
            '%(log_color)s[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s',
            log_colors=log_colors_config
        )
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # ================= 2. 文件输出配置 (按次生成策略) =================
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_dir = os.path.join(root_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)

        # 🚨 核心改造：获取当前运行的精确时间，拼接到文件名里
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file_name = f"run_{current_time}.log"  # 例如: run_2026-04-06_22-55-00.log
        log_file = os.path.join(log_dir, log_file_name)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s')
        file_handler.setFormatter(file_formatter)

        logger.addHandler(file_handler)

    return logger


log = setup_logger()