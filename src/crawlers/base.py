import asyncio
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright
from src.logger import app_logger, error_logger

class BaseCrawler(ABC):
    """すべてのクラウドソーシングクローラーの基底クラス"""
    
    def __init__(self, site_name: str, headless: bool = True):
        self.site_name = site_name
        self.headless = headless
        # クッキー保存ファイルのパス（ログイン状態を維持するため）
        self.state_file = f"src/crawlers/state_{site_name}.json"
        
    @abstractmethod
    async def login(self, page) -> bool:
        """各サイト固有のログイン処理"""
        pass
        
    @abstractmethod
    async def fetch_jobs(self, page, limit: int = 20) -> List[Dict[str, Any]]:
        """各サイト固有の案件一覧取得処理"""
        pass
        
    def filter_web_jobs(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """案件からWeb制作・システム開発関連のものだけをフィルタリングする"""
        keywords = ["web", "ホームページ", "lp", "コーディング", "wordpress", "デザイン", "システム", "開発", "アプリ", "エンジニア", "pm"]
        filtered = []
        for job in jobs:
            text = f"{job.get('title', '')} {job.get('description', '')}".lower()
            if any(k in text for k in keywords):
                filtered.append(job)
        return filtered

    async def run(self) -> List[Dict[str, Any]]:
        """クローラーのメイン実行メソッド"""
        async with async_playwright() as p:
            # ブラウザ起動（ログイン状態保持のためのコンテキスト設定）
            try:
                browser = await p.chromium.launch(headless=self.headless)
                
                # リアルなUser-Agentを設定
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                
                # 過去のログイン状態があれば復元
                import os
                if os.path.exists(self.state_file):
                    context = await browser.new_context(
                        storage_state=self.state_file,
                        user_agent=user_agent
                    )
                    app_logger.info(f"[{self.site_name}] 保存されたログイン状態を使用します。")
                else:
                    context = await browser.new_context(user_agent=user_agent)
                    
                page = await context.new_page()
                
                # ログイン処理
                is_logged_in = await self.login(page)
                if not is_logged_in:
                    error_logger.error(f"[{self.site_name}] ログインに失敗しました。")
                    return []
                    
                # ログイン成功後、状態を保存
                await context.storage_state(path=self.state_file)
                
                # 案件取得
                raw_jobs = await self.fetch_jobs(page, limit=20)
                app_logger.info(f"[{self.site_name}] {len(raw_jobs)}件の案件を取得しました。")
                
                # フィルタリング
                web_jobs = self.filter_web_jobs(raw_jobs)
                app_logger.info(f"[{self.site_name}] Web制作関連として {len(web_jobs)}件 を抽出しました。")
                
                return web_jobs
                
            except Exception as e:
                # デバッグ用にスクリーンショットを保存
                if 'page' in locals():
                    log_dir = os.path.abspath("logs")
                    os.makedirs(log_dir, exist_ok=True)
                    await page.screenshot(path=os.path.join(log_dir, f"error_{self.site_name}.png"))
                error_logger.error(f"[{self.site_name}] スクレイピング実行中にエラー: {str(e)}")
                return []
            finally:
                if 'browser' in locals():
                    await browser.close()
