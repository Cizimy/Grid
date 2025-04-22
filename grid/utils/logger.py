# nvt_ws/utils/logger.py
import logging
import sys
import structlog
from structlog.types import Processor
from ..config import settings # config.pyから設定をインポート

def setup_logging():
    """
    structlogを使用した構造化ロギングを設定する関数。
    コンソールとファイルにJSON形式で出力する。
    """
    log_level = getattr(logging, settings.logging.log_level.upper(), logging.INFO)

    # 標準のloggingとstructlogの連携設定
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(), # 例外発生時のスタックトレース
        structlog.processors.format_exc_info,    # 例外情報の整形
        structlog.processors.UnicodeDecoder(),
    ]

    # structlogの設定
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # フォーマッターの定義 (JSON形式)
    formatter = structlog.stdlib.ProcessorFormatter(
        # Render the final event dict as JSON.
        processor=structlog.processors.JSONRenderer(),
        # foreign_pre_chainは他のライブラリ(例:uvicorn)のログもstructlogで処理する場合
        foreign_pre_chain=shared_processors,
    )

    # 標準loggingハンドラーの設定
    # 1. コンソール出力ハンドラー
    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stdout.setFormatter(formatter)

    # 2. ファイル出力ハンドラー (日付ローテーション)
    # loguru のようなライブラリを使うとローテーションや圧縮がより簡単になる場合がある
    # 標準の TimedRotatingFileHandler を使う例:
    try:
        handler_file = logging.handlers.TimedRotatingFileHandler(
            filename=settings.logging.log_file_path,
            when="midnight", # ローテーション間隔 ('S', 'M', 'H', 'D', 'W0'-'W6', 'midnight')
            interval=1,      # when='D' or 'midnight'なら日数
            backupCount=7,   # 保持するバックアップ数 (log_retention とは少し意味が違う)
            encoding='utf-8',
        )
        handler_file.setFormatter(formatter)
    except Exception as e:
        print(f"Warning: Could not configure file logging: {e}", file=sys.stderr)
        handler_file = None


    # ルートロガーの設定
    root_logger = logging.getLogger()
    # 既存のハンドラーをクリア (重複出力防止)
    # for handler in root_logger.handlers[:]:
    #    root_logger.removeHandler(handler)

    # 新しいハンドラーを追加
    root_logger.addHandler(handler_stdout)
    if handler_file:
        root_logger.addHandler(handler_file)

    root_logger.setLevel(log_level)

    # 他のライブラリのログレベル調整 (必要に応じて)
    # logging.getLogger("flet_core").setLevel(logging.WARNING)
    # logging.getLogger("neo4j").setLevel(logging.INFO)

    print(f"Logging setup complete. Level: {settings.logging.log_level}, File: {settings.logging.log_file_path if handler_file else 'Disabled'}")

# --- アプリケーションでの使用例 ---
# main.py などで最初に呼び出す
# from nvt_ws.utils.logger import setup_logging
# setup_logging()

# ログ出力
# logger = structlog.get_logger(__name__)
# logger.info("Application started", user="default")
# try:
#     1 / 0
# except Exception:
#     logger.exception("An error occurred")