import asyncio
import sys
import subprocess

# WindowsでPlaywrightを正しく動かすための設定
if sys.platform == 'win32':
    # Windowsでサブプロセスをサポートするため、デフォルトのProactorイベントループを使用
    # Python 3.8+ ではデフォルトですが、明示的に設定して不具合を回避します
    import asyncio
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except AttributeError:
        pass # 古いPython環境などのためのフォールバック
import os
from playwright.async_api import async_playwright
from src.logger import app_logger

async def refresh_platform_session(p, site_name, login_url, state_file):
    print(f"\n{'='*50}")
    print(f"【{site_name} のログイン更新】")
    print(f"1. ブラウザが起動します。{site_name}にログインしてください。")
    print(f"2. ロボット判定等があれば手動で解除してください。")
    print(f"3. ログイン完了後、マイページが表示されたらこの画面に戻ってください。")
    print(f"{'='*50}\n")

    browser = await p.chromium.launch(headless=False, executable_path=None)
    # 既存のステートがあれば引き継ぐ（期限切れチェックも含め）
    if os.path.exists(state_file):
        context = await browser.new_context(storage_state=state_file)
    else:
        context = await browser.new_context()

    page = await context.new_page()
    await page.goto(login_url)

    input(f"[{site_name}] ログインが完了したら、ここをクリックして Enter を押してください > ")

    # ステートを保存
    await context.storage_state(path=state_file)
    print(f"[OK] {site_name} のセッションを保存しました: {state_file}")
    
    await browser.close()

async def main():
    sites = [
        {
            "name": "CrowdWorks",
            "url": "https://crowdworks.jp/login",
            "file": "src/crawlers/state_crowdworks.json"
        },
        {
            "name": "Lancers",
            "url": "https://www.lancers.jp/user/login",
            "file": "src/crawlers/state_lancers.json"
        },
        {
            "name": "Coconala",
            "url": "https://coconala.com/login",
            "file": "src/crawlers/state_coconala.json"
        }
    ]

    async with async_playwright() as p:
        for site in sites:
            try:
                await refresh_platform_session(p, site["name"], site["url"], site["file"])
            except Exception as e:
                print(f"[ERROR] {site['name']} の更新中にエラー発生: {e}")

if __name__ == "__main__":
    # Windowsの非同期イベントループポリシー設定 (Proactorを使用)
    if sys.platform == 'win32':
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except AttributeError:
            pass
    asyncio.run(main())
