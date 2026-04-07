import os
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトのルートディレクトリを取得
BASE_DIR = Path(__file__).resolve().parent.parent

# .envファイルのロード
load_dotenv(BASE_DIR / ".env")

class Config:
    # API Keys
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
    GOOGLE_FORM_URL = os.environ.get("GOOGLE_FORM_URL", "")
    
    # Directory Settings
    INPUT_DIR = BASE_DIR / os.environ.get("INPUT_DIR", "data/input")
    ARCHIVE_DIR = BASE_DIR / os.environ.get("ARCHIVE_DIR", "data/archive")
    DB_PATH = BASE_DIR / os.environ.get("DB_PATH", "data/agent.db")
    LOG_DIR = BASE_DIR / "logs"
    PROMPTS_DIR = BASE_DIR / "prompts"
    
    # App Settings
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        """必須設定がロードされているか確認します"""
        missing = []
        if not cls.OPENAI_API_KEY or cls.OPENAI_API_KEY == "your_openai_api_key_here":
            missing.append("OPENAI_API_KEY")
        if not cls.SLACK_WEBHOOK_URL or cls.SLACK_WEBHOOK_URL == "your_slack_webhook_url_here":
            missing.append("SLACK_WEBHOOK_URL")
            
        if missing:
            print(f"Warning: The following required environment variables are missing or default: {', '.join(missing)}")
            print("Please check your .env file.")

# 起動時にディレクトリが存在するか確認し、無ければ作成
Config.INPUT_DIR.mkdir(parents=True, exist_ok=True)
Config.ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
Config.LOG_DIR.mkdir(parents=True, exist_ok=True)
Config.PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
Config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
