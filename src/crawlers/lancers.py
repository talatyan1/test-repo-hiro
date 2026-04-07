from src.crawlers.base import BaseCrawler
import asyncio
from typing import List, Dict, Any

class LancersCrawler(BaseCrawler):
    def __init__(self, headless: bool = True):
        super().__init__(site_name="lancers", headless=headless)
        self.login_url = "https://www.lancers.jp/user/login"
        self.jobs_url = "https://www.lancers.jp/work/search/web?open=1&sort=new" # Web制作・募集中 (新着順)
        
    async def login(self, page) -> bool:
        """ランサーズへのログイン状態確認"""
        await page.goto(self.jobs_url)
        await asyncio.sleep(2)
        
        # ログインボタンがあるか確認（あれば未ログイン）
        login_btn = page.locator('a[href*="/user/login"], .c-nav-main__link--login').first
        if await login_btn.count() > 0 and await login_btn.is_visible():
            from src.logger import error_logger
            error_logger.error("ランサーズ: ログイン状態が解除されています。手動でログインして state_lancers.json を更新してください。")
            return False
            
        return True
        
    async def fetch_jobs(self, page, limit: int = 20) -> List[Dict[str, Any]]:
        """ランサーズで最新案件を取得"""
        jobs = []
        await page.goto(self.jobs_url)
        await asyncio.sleep(2) # 読み込み待ち
        
        # JavaScript実行による直接抽出 (Lancers用)
        jobs_data = await page.evaluate("""() => {
            const items = Array.from(document.querySelectorAll('.c-media, [class*="search-job-item"]'));
            return items.map(el => {
                const titleEl = el.querySelector('a[href*="/work/detail/"]');
                const priceEl = el.querySelector('.c-media__job-price, [class*="price"]');
                const descEl = el.querySelector('.c-media__job-detail, [class*="description"]');
                
                return {
                    title: titleEl ? titleEl.innerText.trim() : '',
                    url: titleEl ? titleEl.href : '',
                    reward: priceEl ? priceEl.innerText.trim() : '不明',
                    description: descEl ? descEl.innerText.trim() : ''
                };
            }).filter(j => j.title && j.url);
        }""")
        
        for data in jobs_data[:limit]:
            try:
                job_data = {
                    "platform": self.site_name,
                    "title": data["title"],
                    "url": data["url"],
                    "reward": data["reward"],
                    "description": data["description"]
                }
                jobs.append(job_data)
            except Exception as e:
                continue
                
        return jobs
