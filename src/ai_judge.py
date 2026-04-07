import json
from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from src.config import Config
from src.logger import ai_logger, error_logger
from src.db import Job

# OpenAIクライアントの初期化
client = OpenAI(api_key=Config.OPENAI_API_KEY)

class AIJudge:
    def __init__(self):
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = Config.PROMPTS_DIR / "judge_prompt.txt"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            error_logger.error(f"judge_prompt.txt の読み込みに失敗しました: {e}")
            return "Web制作案件かどうかを判定し、{'is_matched': true/false, 'reason': '...'} のJSON形式で返してください。"

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def evaluate_job(self, job: Job) -> dict:
        """
        案件情報を受け取り、対応可能か判定します。
        戻り値: {"is_matched": bool, "reason": str}
        """
        if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY == "your_openai_api_key_here":
            error_logger.error("OpenAI APIキーが設定されていないため、AI判定をスキップします。")
            return {"is_matched": False, "reason": "API Key Error"}

        prompt = self.prompt_template.format(
            title=job.title,
            description=job.description[:1000],  # トークン節約のため先頭1000文字で制限
            reward=job.reward
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini", # コストパフォーマンスが良いモデル
                messages=[
                    {"role": "system", "content": "出力は必ず指定されたJSONフォーマットのみにしてください。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1, # 決定論的な結果を期待
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)
            
            ai_logger.info(f"案件({job.job_url})判定: {result_json['is_matched']} (理由: {result_json.get('reason', '')})")
            return result_json
            
        except json.JSONDecodeError as e:
            ai_logger.error(f"AIのJSONレスポンス解析エラー (案件: {job.job_url}): {result_text}")
            return {"is_matched": False, "reason": "JSON Parse Error"}
        except Exception as e:
            error_logger.error(f"AI APIリクエストエラー (案件: {job.job_url}): {e}")
            raise e # retryデコレータによりリトライさせる
