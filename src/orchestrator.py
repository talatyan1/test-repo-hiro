from src.ai_judge import AIJudge
from src.proposal_generator import ProposalGenerator
from src.crawlers.crowdworks import CrowdWorksCrawler
from src.crawlers.lancers import LancersCrawler
from src.crawlers.coconala import CoconalaCrawler
from src.agent_actions import AgentActions
from src.logger import app_logger
from src.slack_notifier import SlackNotifier
import asyncio
import time

class Orchestrator:
    def __init__(self):
        self.ai = AIJudge()
        self.actions = AgentActions(headless=True)
        self.slack = SlackNotifier()
        # 各クローラー、ジェネレータの初期化
        self.crawlers = [
            CrowdWorksCrawler(),
            LancersCrawler(),
            CoconalaCrawler()
        ]

    def run(self):
        app_logger.info("オーケストレーター起動")
        for crawler in self.crawlers:
            try:
                jobs = crawler.fetch_jobs()
                for job in jobs:
                    # 重複チェック（DB/Sheets）
                    if self._is_new_job(job):
                        match_result = self.ai.judge(job)
                        if match_result["match_score"] >= 70:
                            self._process_application(job, match_result)
            except Exception as e:
                app_logger.error(f"{crawler.name} 実行中にエラー: {e}")

    def _is_new_job(self, job):
        # 簡易実装（本来はDBからチェック）
        return True

    def _process_application(self, job, match_result):
        # 提案文生成
        generator = ProposalGenerator()
        proposal_text = generator.generate(job, match_result)
        
        # 応募実行
        success, message = asyncio.run(self.actions.apply(job, proposal_text))
        
        # 通知
        self.slack.notify(f"【応募{'成功' if success else '失敗'}】\n案件: {job['title']}\nURL: {job['url']}\n理由: {message}")
