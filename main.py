import asyncio
import os
import sys

# WindowsでPlaywrightを安定して動かすための設定
if sys.platform == 'win32':
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except AttributeError:
        pass

from src.orchestrator import Orchestrator
from src.logger import app_logger

def main():
    try:
        app_logger.info("Starting Crowd Agent...")
        
        # 設定のバリデーション (環境変数の不足チェック)
        from src.config import Config
        Config.validate()
        
        # メイン処理の実行
        orchestrator = Orchestrator()
        orchestrator.run()
        
    except KeyboardInterrupt:
        app_logger.info("処理が手動で中断されました。")
        sys.exit(0)
    except Exception as e:
        app_logger.error(f"致命的なエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
