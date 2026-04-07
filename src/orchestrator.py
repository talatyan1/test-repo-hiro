import asyncio
from src.db import SessionLocal
from src.excel_reader import ExcelReader
from src.deduplicator import Deduplicator
from src.ai_judge import AIJudge
from src.proposal_generator import ProposalGenerator
from src.slack_notifier import SlackNotifier
from src.email_notifier import EmailNotifier
from src.crawlers.crowdworks import CrowdWorksCrawler
from src.crawlers.lancers import LancersCrawler
from src.crawlers.coconala import CoconalaCrawler
from src.agent_actions import AgentActions
from src.logger import app_logger

class Orchestrator:
    def __init__(self):
        self.reader = ExcelReader()
        self.ai_judge = AIJudge()
        self.generator = ProposalGenerator()
        self.notifier = SlackNotifier()
        self.email_notifier = EmailNotifier()
        # 自動応募を可視化 (ユーザーが補助可能な状態にするため headless=False)
        self.actions = AgentActions(headless=False)

    def run(self):
        """全体のフローを実行します"""
        app_logger.info("=== クラウドソーシング自動化処理を開始します ===")
        
        db_session = SessionLocal()
        stats = {
            "total_scraped": 0,
            "new_jobs": 0,
            "matches": 0,
            "applied": 0,
            "platforms": ["crowdworks", "lancers", "coconala"]
        }
        
        try:
            dedup = Deduplicator(db_session)
            
            # --- フェーズ1: スクレイピング ---
            app_logger.info("[*] 各クラウドソーシングサイトを巡回中...")
            
            crawlers = [
                CrowdWorksCrawler(headless=False),
                LancersCrawler(headless=False),
                CoconalaCrawler(headless=False)
            ]
            
            scraped_jobs = []
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            for crawler in crawlers:
                try:
                    jobs = loop.run_until_complete(crawler.run())
                    if jobs:
                        scraped_jobs.extend(jobs)
                        app_logger.info(f"[{crawler.site_name}] {len(jobs)} 件取得")
                except Exception as e:
                    app_logger.error(f"[{crawler.site_name}] 巡回中にエラー: {e}")
            
            if scraped_jobs:
                stats["total_scraped"] = len(scraped_jobs)
                dedup.process_new_jobs(scraped_jobs)
                app_logger.info(f"全サイト合計: {len(scraped_jobs)} 件取得（重複排除前）")
            else:
                app_logger.warning("スクレイピングで案件が取得できませんでした。")

            # --- フェーズ2: 未処理案件のAI判定と提案生成・応募 ---
            unprocessed_jobs = dedup.get_unprocessed_jobs()
            stats["new_jobs"] = len(unprocessed_jobs)
            app_logger.info(f"AI判定待ちの新規案件: {len(unprocessed_jobs)} 件")

            for job in unprocessed_jobs:
                try:
                    # AI判定が必要な場合のみ実行
                    if job.status == "new":
                        judge_result = self.ai_judge.evaluate_job(job)
                        is_matched = judge_result.get("is_matched", False)
                        reason = judge_result.get("reason", "")
                        # ステータスを一度 judged に更新
                        dedup.mark_as_processed(job, is_matched, None, reason)
                    else:
                        # 既に judged の場合はDBから情報を取得
                        is_matched = (job.ai_judge_result == "matched")
                        reason = job.ai_judge_reason

                    if is_matched and not job.is_applied:
                        stats["matches"] += 1
                        app_logger.info(f"[MATCH/RETRY] {job.title} - {reason}")
                        
                        # 提案文の生成 (未生成の場合のみ)
                        proposal_text = job.proposal_text
                        if not proposal_text:
                            proposal_text = self.generator.generate_proposal(job)
                            # 提案文のみを途中で保存
                            job.proposal_text = proposal_text
                            db_session.commit()
                        
                        # --- 自動応募の実行 ---
                        success = False
                        msg = "不明なエラー"
                        try:
                            if job.platform == "crowdworks":
                                success, msg = loop.run_until_complete(self.actions.apply_to_crowdworks(job.job_url, proposal_text, job.reward))
                            elif job.platform == "lancers":
                                success, msg = loop.run_until_complete(self.actions.apply_to_lancers(job.job_url, proposal_text, job.reward))
                            elif job.platform == "coconala":
                                success, msg = loop.run_until_complete(self.actions.apply_to_coconala(job.job_url, proposal_text, job.reward))
                        except Exception as apply_err:
                            msg = f"例外発生: {apply_err}"
                            app_logger.error(f"応募処理の実行中に例外が発生しました: {apply_err}")

                        if success:
                            stats["applied"] += 1
                        
                        # 応募ステータスをDBに記録
                        dedup.mark_as_applied(job, success, msg)
                        
                        # 報告と通知
                        status_str = "success" if success else "failed"
                        app_logger.info(f"[{job.platform}] 応募実行結果: {status_str} - {msg} ({job.job_url})")
                        
                        # Slack個別通知 (結果に関わらず通知)
                        self.notifier.send_application_notification(job, success, error_message=msg)
                        if success:
                            self.email_notifier.send_application_report(job, status_str)
                
                except Exception as e:
                    app_logger.error(f"案件({job.job_url})の処理中にエラー: {e}")

            loop.close()

        except Exception as e:
            app_logger.error(f"予期せぬエラーで処理が中断しました: {e}")
        finally:
            # 処理終了後のサマリー通知
            try:
                self.notifier.send_run_summary(stats)
            except:
                pass
            db_session.close()
            
        app_logger.info("=== 処理が正常に完了しました ===")
