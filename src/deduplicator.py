from sqlalchemy.orm import Session
from src.db import Job
from src.logger import app_logger

class Deduplicator:
    def __init__(self, db_session: Session):
        self.db = db_session

    def process_new_jobs(self, jobs_data: list[dict]) -> list[Job]:
        """
        抽出された案件リストを受け取り、DBに存在しない新規案件のみを登録して返します。
        
        jobs_data format:
        [
            {
                "site": "crowdworks",
                "title": "Web制作のお願い",
                "url": "https://crowdworks.jp/public/jobs/12345",
                "reward": "10000円",
                "description": "LP制作をお願いします...",
                "deadline": "2023-12-31",
                "client_info": "株式会社テスト"
            }, ...
        ]
        """
        new_jobs = []
        seen_in_this_run = set()
        
        for data in jobs_data:
            # URLがユニークキーになると想定
            url = data.get("url", "").strip()
            if not url or url in seen_in_this_run:
                continue
            seen_in_this_run.add(url)
                
            # DBに既に存在するかチェック
            exists = self.db.query(Job).filter(Job.job_url == url).first()
            if exists:
                continue # すでに取得済みの案件はスキップ
                
            # 新規案件の登録
            # クローラー側が 'platform'、デデュープリケーター側が 'site' を期待している可能性を考慮
            site_name = data.get("platform") or data.get("site", "unknown")
            
            new_job = Job(
                platform=site_name,
                title=data.get("title", ""),
                job_url=url,
                reward=data.get("reward", ""),
                description=data.get("description", ""),
                deadline=data.get("deadline", ""),
                client_name=data.get("client_info", ""),
                status="new",
                notified=0
            )
            
            self.db.add(new_job)
            new_jobs.append(new_job)
            
        # コミットして保存
        if new_jobs:
            try:
                self.db.commit()
                app_logger.info(f"DBに {len(new_jobs)} 件の新規案件を登録しました。")
            except Exception as e:
                self.db.rollback()
                app_logger.error(f"新規案件のDB登録中にエラーが発生しました: {e}")
                return []
        
        return new_jobs

    def get_unprocessed_jobs(self) -> list[Job]:
        """
        AI判定待ち、またはマッチしたが未応募の案件を取得します。
        """
        from sqlalchemy import or_
        return self.db.query(Job).filter(
            or_(
                Job.status == "new",
                (Job.status == "judged") & (Job.ai_judge_result == "matched") & (Job.is_applied == False)
            )
        ).all()

    def mark_as_processed(self, job: Job, is_matched: bool = False, proposal_text: str | None = None, match_reason: str | None = None):
        """
        AI判定完了マークを付けます
        """
        job.status = "judged"
        job.ai_judge_result = "matched" if is_matched else "unmatched"
        job.ai_judge_reason = match_reason
        
        if proposal_text:
            job.proposal_text = proposal_text
            
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            app_logger.error(f"案件({job.job_url})のステータス更新中にエラーが発生しました: {e}")

    def mark_as_applied(self, job: Job, success: bool, error_message: str | None = None):
        """
        応募実行結果を記録します
        """
        job.is_applied = success
        job.application_error = error_message if not success else None
        
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            app_logger.error(f"案件({job.job_url})の応募ステータス更新中にエラーが発生しました: {e}")
