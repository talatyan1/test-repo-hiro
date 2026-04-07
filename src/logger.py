import logging
import logging.handlers
from pathlib import Path
from src.config import Config

def setup_logger(name: str, log_file: str) -> logging.Logger:
    """
    指定された名前とファイル名でロガーをセットアップします
    """
    logger = logging.getLogger(name)
    # すでにハンドラが設定されている場合は何もしない（二重登録防止）
    if logger.handlers:
        return logger

    # ログレベルの設定
    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # ログフォーマット
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # ファイルハンドラ (ローテーション付き: 5MBでローテーション、3世代分保持)
    log_path = Config.LOG_DIR / log_file
    file_handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# 主要なロガーを定義
app_logger = setup_logger('app_logger', 'app.log')
ai_logger = setup_logger('ai_logger', 'ai.log')
error_logger = setup_logger('error_logger', 'error.log')
