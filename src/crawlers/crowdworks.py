from src.crawlers.base import BaseCrawler
import asyncio
import os
from typing import List, Dict, Any
from src.logger import app_logger

class CrowdWorksCrawler(BaseCrawler):
    def __init__(self, headless: bool = True):
        super().__init__(site_name="crowdworks", headless=headless)
        self.login_url = "https://crowdworks.jp/login"
        self.jobs_url = "https://crowdworks.jp/public/jobs/search?category_id=230&hide_expired=true&order=new" # Web制作・募集中 (新着順)
        
    async def login(self, page) -> bool:
        """クラウドワークスへのログイン"""
        # ※実際の現場では、環境変数からID/Passを取得するか、Cookieが有効かチェックします。
        # 今回のMVPでは、「ログイン状態」を作る処理の枠組みとして定義します。
        
        # 既にログインしているかチェック
        await page.goto(self.jobs_url)
        # 一定秒数待機し、ログインボタンがなければログイン済みと判定する等の処理を実装
        return True
        
    async def fetch_jobs(self, page, limit: int = 20) -> List[Dict[str, Any]]:
        """クラウドワークスで最新案件を取得"""
        jobs = []
        await page.goto(self.jobs_url)
        
        # 新着順でソート (URLパラメータに order=new 等を含めるなど)
        await asyncio.sleep(5) # 基礎的な待機
        # 案件要素の待機をより柔軟に
        try:
            await page.wait_for_selector('a[href*="/public/jobs/"]', timeout=20000)
        except:
            app_logger.warning("案件リンクが見つかりませんでした。")
            log_dir = os.path.abspath("logs")
            os.makedirs(log_dir, exist_ok=True)
            await page.screenshot(path=os.path.join(log_dir, "error_crowdworks.png"))
            return []

        # JavaScript実行による直接抽出
        jobs_data = await page.evaluate(r"""() => {
            // 案件リンクの特定 (部分一致セレクタを活用)
            const jobLinks = Array.from(document.querySelectorAll('a[href*="/public/jobs/"]'));
            const uniqueJobs = [];
            const seenUrls = new Set();

            jobLinks.forEach(link => {
                const url = link.href;
                if (!url || seenUrls.has(url) || url.includes('/new') || url.includes('/category/')) return;
                seenUrls.add(url);

                // 案件詳細URLのみを対象とする (例: /public/jobs/1234567)
                if (!url.match(/\/public\/jobs\/\d+/)) return;

                // 案件タイトル要素の取得 (クラス名に 'title' を含むものを優先)
                const titleText = link.innerText.trim();
                if (titleText.length < 5) return;

                // 親要素（案件カード全体）の特定。h3などの見出しを持つ親コンテナを探す
                let card = link.closest('[class*="item"]') || link.closest('div[style*="border"]') || link.parentElement.parentElement;
                
                // 報酬金額の抽出 (金額記号や '円' を含む要素を探す)
                let reward = '不明';
                if (card) {
                    const priceEl = card.querySelector('[class*="price"], [class*="amount"]');
                    if (priceEl) reward = priceEl.innerText.trim();
                }

                // 詳細説明の抽出
                let description = '';
                if (card) {
                    const descEl = card.querySelector('[class*="description"], [class*="summary"], [class*="body"]');
                    if (descEl) description = descEl.innerText.trim();
                }

                uniqueJobs.push({
                    title: titleText,
                    url: url,
                    reward: reward,
                    description: description
                });
            });
            return uniqueJobs;
        }""")
        
        for data in jobs_data[:limit]:
            try:
                # URLの補完
                url = data["url"]
                if url and url.startswith('/'):
                    url = f"https://crowdworks.jp{url}"
                    
                job_data = {
                    "platform": self.site_name,
                    "title": data["title"],
                    "url": url,
                    "reward": data["reward"],
                    "description": data["description"]
                }
                jobs.append(job_data)
            except Exception as e:
                continue
                
        return jobs
