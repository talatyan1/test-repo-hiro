from src.crawlers.base import BaseCrawler
import asyncio
from typing import List, Dict, Any

class CoconalaCrawler(BaseCrawler):
    def __init__(self, headless: bool = True):
        super().__init__(site_name="coconala", headless=headless)
        self.login_url = "https://coconala.com/login"
        self.jobs_url = "https://coconala.com/requests/categories/22?recruiting=true" # Web制作・募集中 (新着順)
        
    async def login(self, page) -> bool:
        """ココナラへのログイン状態確認とモード切替"""
        await page.goto(self.jobs_url)
        await asyncio.sleep(2)
        
        # 受注モードへの切替ボタンがあればクリック
        # セレクタ: .c-header_modeSwitchItem, a:has-text("受注モードへ切替")
        mode_switch = page.locator('a:has-text("受注モードへ切替"), .c-header_modeSwitchItem').first
        if await mode_switch.count() > 0:
            app_logger.info("ココナラ: 受注モードに切り替えます...")
            await mode_switch.click()
            await asyncio.sleep(3)
            
        return True
        
    async def fetch_jobs(self, page, limit: int = 20) -> List[Dict[str, Any]]:
        """ココナラで最新案件を取得"""
        jobs = []
        await page.goto(self.jobs_url)
        await asyncio.sleep(2) # 読み込み待ち
        
        # JavaScript実行による直接抽出 (Coconala用)
        jobs_data = await page.evaluate(r"""() => {
            const items = Array.from(document.querySelectorAll('.c-searchItem, [class*="searchItem"]'));
            return items.map(el => {
                const titleEl = el.querySelector('a[href*="/requests/"]');
                const url = titleEl ? titleEl.href : '';
                const priceEl = el.querySelector('[class*="price"], [class*="Price"]');
                const descEl = el.querySelector('[class*="description"], [class*="body"], [class*="Content"]');
                
                // 案件詳細URLのみを対象とする (例: /requests/12345)
                if (!url || !url.includes('/requests/') || url.includes('/categories/') || url.match(/\/requests\/\w+\//)) return null;
                
                return {
                    title: titleEl ? titleEl.innerText.trim() : '',
                    url: url,
                    reward: priceEl ? priceEl.innerText.trim() : '不明',
                    description: descEl ? descEl.innerText.trim() : ''
                };
            }).filter(j => j && j.title && j.url);
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
