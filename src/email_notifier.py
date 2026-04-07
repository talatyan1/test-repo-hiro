import smtplib
from email.message import EmailMessage
import os
from src.config import Config
from src.logger import app_logger, error_logger
from src.db import Job

class EmailNotifier:
    def __init__(self):
        self.sender_email = os.environ.get("GMAIL_ADDRESS")
        self.app_password = os.environ.get("GMAIL_APP_PASSWORD")
        self.report_recipient = self.sender_email # 自分宛に送ると想定

    def send_application_report(self, job: Job, status: str, error_msg: str = None):
        """
        応募が実行された際、その詳細をユーザーへメールで即時に報告します。
        """
        if not self.sender_email or not self.app_password:
            app_logger.warning("メール送信に必要な環境変数が不足しているため、応募報告メールをスキップします。")
            return False

        msg = EmailMessage()
        status_text = "【成功】" if status == "success" else "【失敗】"
        msg['Subject'] = f"{status_text} 案件応募報告 ({job.platform}) - {job.title[:20]}..."
        msg['From'] = self.sender_email
        msg['To'] = self.report_recipient

        content = f"""お疲れ様です。
クラウドソーシング・エージェントより、以下の案件への応募（提案送信）を試行しました。

■ 応募結果: {status_text}
{f"■ エラー内容: {error_msg}" if error_msg else ""}

■ 案件詳細
- プラットフォーム: {job.platform}
- タイトル: {job.title}
- 報酬: {job.reward}
- 案件URL: {job.job_url}

■ 送信した提案文
--------------------------------------------------
{job.proposal_text or "(提案文なし)"}
--------------------------------------------------

引き続き、他の案件についても監視を継続します。
"""
        msg.set_content(content)

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
                smtp.login(self.sender_email, self.app_password)
                smtp.send_message(msg)
            app_logger.info(f"案件({job.job_url})の応募報告メールを送信しました。")
            return True
        except Exception as e:
            error_logger.error(f"応募報告メールの送信に失敗しました: {e}")
            return False
