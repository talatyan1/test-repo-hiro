
import asyncio
import os
import sys
from playwright.async_api import async_playwright
from src.agent_actions import AgentActions
from src.logger import app_logger

async def process_lancers_pending():
    """Lancersの提案アシスト(確認待ち)を直接処理する"""
    app_logger.info("Lancers 提案アシストの保留案件処理を開始します...")
    
    # Windows用のイベントループ設定
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    async with async_playwright() as p:
        # headless=False でユーザーが見えるようにする
        browser = await p.chromium.launch(headless=False)
        
        # 保存されたセッションを読み込む
        storage_state = "src/crawlers/state_lancers.json"
        if not os.path.exists(storage_state):
            app_logger.error(f"セッションファイルが見つかりません: {storage_state}")
            await browser.close()
            return

        context = await browser.new_context(storage_state=storage_state)
        page = await context.new_page()
        
        try:
            # 提案アシスト管理画面へ
            await page.goto("https://www.lancers.jp/auto_proposal")
            await asyncio.sleep(3)
            
            # 各設定の「確認待ち」の数字（リンク）を探す
            pending_links = page.locator('a[href$="/pending"]')
            count = await pending_links.count()
            
            if count == 0:
                app_logger.info("確認待ちの案件は見つかりませんでした。")
                await browser.close()
                return

            app_logger.info(f"{count} 個の提案アシスト設定から保留案件を確認します。")
            
            # 最初の設定の「確認待ち」ページへ (デモンストレーションとして1つずつ処理)
            for i in range(count):
                await pending_links.nth(i).click()
                await asyncio.sleep(3)
                
                # 「確認待ち」リスト内の「確認する」ボタンを取得
                # クラス名: _confirmButton_e38c9_329
                confirm_btns = page.locator('button:has-text("確認する")')
                btn_count = await confirm_btns.count()
                
                if btn_count == 0:
                    app_logger.info("このページに『確認する』ボタンが見つかりません。次へ進みます。")
                    await page.goto("https://www.lancers.jp/auto_proposal")
                    continue
                
                app_logger.info(f"現在のページで {btn_count} 件の保留案件が見つかりました。")
                
                # 各案件を処理
                for j in range(btn_count):
                    # 各「確認する」ボタンをクリック (モーダルまたは遷移)
                    # 常に最初のボタン（リストの上位）から処理
                    target_btn = confirm_btns.first
                    await target_btn.click()
                    await asyncio.sleep(2)
                    
                    # モーダル内の「提案する（提案作成画面へ）」ボタンをクリック
                    propose_btn = page.locator('button:has-text("提案する（提案作成画面へ）")')
                    if await propose_btn.count() > 0:
                        await propose_btn.click()
                        await asyncio.sleep(3)
                        
                        # 通常の提案画面に遷移したので、既存のAgentActionsを使って応募を実行
                        current_url = page.url
                        app_logger.info(f"提案フォームに到達: {current_url}")
                        
                        actions = AgentActions(headless=False)
                        # ダミー情報を一部使ってフォームを埋める (本来はOrchestratorから渡すべきだが今回はスタンドアロン)
                        # proposal_text は適宜
                        success, msg = await actions.apply_to_lancers(page, current_url, "10000", "AI提案アシスト経由の応募です。")
                        
                        if success:
                            app_logger.info("成功しました！次の案件へ。")
                        else:
                            app_logger.warning(f"失敗: {msg}")
                        
                        # 次の案件のために管理画面に戻る
                        await page.goto("https://www.lancers.jp/auto_proposal")
                        await asyncio.sleep(2)
                        # 設定ページに再度入る
                        await pending_links.nth(i).click()
                        await asyncio.sleep(2)
                        # ボタンを再取得
                        confirm_btns = page.locator('button:has-text("確認する")')
                    else:
                        app_logger.warning("『提案作成画面へ』ボタンが見つかりませんでした。")
                        await page.go_back()

        except Exception as e:
            app_logger.error(f"エラー発生: {str(e)}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(process_lancers_pending())
