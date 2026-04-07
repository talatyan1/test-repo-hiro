import json
import requests
from src.config import Config
from src.logger import app_logger, error_logger
from src.db import Job

class SlackNotifier:
    def __init__(self):
        self.webhook_url = Config.SLACK_WEBHOOK_URL

    def send_matched_job_notification(self, job: Job, match_reason: str):
        """
        AIが対応可能と判定した案件をSlackに通知します
        """
        if not self.webhook_url or self.webhook_url == "your_slack_webhook_url_here":
            app_logger.warning("Slack Webhook URLが設定されていないため,通知をスキップします。")
            return

        # Slack Block Kit フォーマットでのメッセージ構築
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🎉 新規マッチ案件: {job.title[:30]}..."
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*サイト:*\\n{job.platform}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*報酬:*\\n{job.reward}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*🤖 AI判定理由:*\\n{match_reason}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{job.job_url}|案件詳細ページを開く>"
                }
            },
            {"type": "divider"}
        ]

        # 提案文があれば追加
        if job.proposal_text:
            blocks.extend([
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*📝 AI生成 提案テンプレート:*"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```\\n{job.proposal_text}\\n```"
                    }
                }
            ])

        payload = {"blocks": blocks}

        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            # DBのnotifiedフラグを更新
            job.notified = 1
            app_logger.info(f"案件({job.job_url})のSlack通知を送信しました。")
        except requests.exceptions.RequestException as e:
            error_logger.error(f"Slack通知の送信に失敗しました (案件: {job.job_url}): {e}")

    def send_application_notification(self, job: Job, success: bool, error_message: str = None):
        """
        応募実行結果をSlackに通知します
        """
        if not self.webhook_url or self.webhook_url == "your_slack_webhook_url_here":
            return

        status_text = "✅ 応募成功" if success else "❌ 応募失敗"
        if not success and "セッション切れ" in (error_message or ""):
            status_text = "⚠️ セッション切れ（重要）"

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{status_text}: {job.title[:30]}..."}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*案件:* <{job.job_url}|{job.title}>"}
            }
        ]

        if not success:
            msg = f"*エラー詳細:*\\n{error_message}"
            if "セッション切れ" in (error_message or ""):
                msg += "\\n\\n> [!IMPORTANT]\\n> `refresh_sessions.py` を実行してログイン状態を更新してください。"
            
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": msg}
            })

        payload = {"blocks": blocks}

        try:
            requests.post(self.webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
            app_logger.info(f"応募結果通知を送信しました: {job.job_url}")
        except Exception as e:
            error_logger.error(f"応募結果通知の送信に失敗しました: {e}")

    def send_run_summary(self, stats: dict):
        """
        実行結果のサマリーをSlackに通知します（生存確認も兼ねる）
        """
        if not self.webhook_url or self.webhook_url == "your_slack_webhook_url_here":
            return

        total_scraped = stats.get("total_scraped", 0)
        new_jobs = stats.get("new_jobs", 0)
        matches = stats.get("matches", 0)
        applied = stats.get("applied", 0)
        platforms = ", ".join(stats.get("platforms", []))

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 クラウドソーシング監視 Report"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*巡回状況:* 正常に監視中です。\\n*対象サイト:* {platforms}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*取得案件:* {total_scraped} 件"},
                    {"type": "mrkdwn", "text": f"*新規案件:* {new_jobs} 件"},
                    {"type": "mrkdwn", "text": f"*AIマッチ:* {matches} 件"},
                    {"type": "mrkdwn", "text": f"*自動応募:* {applied} 件"}
                ]
            },
            {"type": "divider"}
        ]

        # マッチ案件がない場合のメッセージ
        if matches == 0:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_※現在,条件に合致する新着案件は見つかりませんでした。引き続き24時間体制で監視を継続します。_"
                }
            })

        payload = {"blocks": blocks}

        try:
            requests.post(self.webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
            app_logger.info("実行結果サマリーをSlackに送信しました。")
        except Exception as e:
            error_logger.error(f"サマリー通知の送信に失敗しました: {e}")
