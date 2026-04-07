from openai import OpenAI
from tenacity import retry, wait_exponential, stop_after_attempt
from src.config import Config
from src.logger import ai_logger, error_logger
from src.db import Job

client = OpenAI(api_key=Config.OPENAI_API_KEY)

class ProposalGenerator:
    def __init__(self):
        self.prompt_template = self._load_prompt()

    def _load_prompt(self) -> str:
        prompt_path = Config.PROMPTS_DIR / "proposal_prompt.txt"
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            error_logger.error(f"proposal_prompt.txt の読み込みに失敗しました: {e}")
            return "適切な提案文を作成してください。"

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def generate_proposal(self, job: Job) -> str:
        """
        AI判定で対応可能とされた案件に対して、具体的な提案文言を生成します。
        """
        if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY == "your_openai_api_key_here":
            return "(APIキーが未設定のため、提案文は生成されませんでした)"

        prompt = self.prompt_template.format(
            title=job.title,
            description=job.description[:1500], # トークン上限対策
            client_info=job.client_name,
            google_form_url=Config.GOOGLE_FORM_URL or "(GoogleフォームURL未設定)"
        )

        try:
            response = client.chat.completions.create(
                model="gpt-4o", # 提案文作成はより高度な推論が求められるため4oなどを使用
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7 # 表現力を持たせるため少し高め
            )
            
            proposal_text = response.choices[0].message.content.strip()
            ai_logger.info(f"案件({job.job_url})の提案文生成完了 (文字数: {len(proposal_text)})")
            
            return proposal_text
            
        except Exception as e:
            error_logger.error(f"提案文の生成中にエラーが発生しました (案件: {job.job_url}): {e}")
            raise e
