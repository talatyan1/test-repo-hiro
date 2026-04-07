
import asyncio
import os
import sys
import gspread
from playwright.async_api import async_playwright
from src.logger import app_logger

# パス追加
sys.path.append(os.getcwd())

SPREADSHEET_ID = "1xALyErlbTB7P32gf8b4qq4JY70FYxnA7PPOiMvHIK6U"

async def reply_to_platform(job_url, result_url):
    """
    案件URLを分析し、適切なプラットフォームのメッセージ欄にサイトURLを投稿する。
    """
    app_logger.info(f"[*] プラットフォーム自動返信開始: {job_url}")
    
    if "coconala.com" in job_url:
        return await reply_coconala(job_url, result_url)
    elif "lancers.jp" in job_url:
        return await reply_lancers(job_url, result_url)
    elif "crowdworks.jp" in job_url:
        return await reply_crowdworks(job_url, result_url)
    else:
        app_logger.error(f"[-] 未知のプラットフォーム: {job_url}")
        return False

async def reply_coconala(job_url, result_url):
    state_file = "src/crawlers/state_coconala.json"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        if os.path.exists(state_file):
            context = await browser.new_context(storage_state=state_file)
        else:
            context = await browser.new_context()
        
        page = await context.new_page()
        try:
            app_logger.info(f"[*] 案件ページへ遷移: {job_url}")
            await page.goto(job_url)
            await asyncio.sleep(5)
            
            # --- 「応募済み」ボタンを探してクリック ---
            # 新しいタブが開く可能性があるため、context.expect_page() を使用
            applied_link = page.locator('a:has-text("応募済み"), .p-requestDetail__offerAction a:has-text("応募済み")').first
            
            if await applied_link.count() > 0:
                app_logger.info("[*] 「応募済み」ボタンを特定。編集ページへ移動します...")
                try:
                    async with context.expect_page(timeout=10000) as new_page_info:
                        await applied_link.click()
                    target_page = await new_page_info.value
                except:
                    # タブが開かなかった場合は現在のページで継続
                    target_page = page
                
                # ネットワークの静止を待たずに、要素の出現を直接待つ
                app_logger.info("[*] 編集エリアの出現を待機中...")
                try:
                    await target_page.wait_for_selector('textarea.js_offers-content, textarea#OfferContent', timeout=15000)
                except:
                    app_logger.warning("[!] タイムアウトしましたが、続行を試みます。")
                
                await asyncio.sleep(2)
                
                # --- 提案編集エリア（Textarea）の操作 ---
                # 要素が見えるまでスクロール
                message_box = target_page.locator('textarea.js_offers-content, textarea#OfferContent').first
                if await message_box.count() > 0:
                    await message_box.scroll_into_view_if_needed()
                    current_text = await message_box.input_value()
                    
                    reply_intro = (
                        "【🎉 プロジェクトの試作品（プロトタイプ）が完成いたしました！】\n"
                        "ヒアリング内容に基づき、早速スピード作成いたしました。以下のリンクよりご確認いただけます。\n\n"
                        f"✨ 試作品プレビューURL： {result_url}\n\n"
                        "--------------------------------------------------\n"
                    )
                    
                    if result_url not in current_text:
                        # 既存テキストの冒頭に追加
                        await message_box.fill(reply_intro + current_text)
                        app_logger.info("[+] 提案内容のアップデート（URL追記）を完了。")
                    else:
                        app_logger.warning("[!] 既にURLが追記済みです。")
                        return True
                    
                    await asyncio.sleep(2)
                    
                    # --- 更新・確定ボタン ---
                    submit_btn = target_page.locator('.js_offers-button').first
                    if await submit_btn.count() > 0:
                        app_logger.info("[!] 「確認画面に進む」をクリックします。")
                        await submit_btn.click()
                        await asyncio.sleep(3)
                        
                        # 最終送信（もしあれば）
                        final_btn = target_page.locator('.js_offers-button:has-text("送信"), button:has-text("送信")').first
                        if await final_btn.count() > 0:
                            await final_btn.click()
                            app_logger.info("✅ ココナラ：メッセージの送信（更新）を完了しました！")
                            await asyncio.sleep(5)
                            return True
                        else:
                            app_logger.info("✅ ココナラ：更新が直接反映されました。")
                            return True
                else:
                    app_logger.error("[-] ココナラ：編集用 textarea が見つかりませんでした。")
                    await target_page.screenshot(path="logs/screenshots/coconala_error_no_textarea.png")
            else:
                app_logger.error("[-] ココナラ：「応募済み」ボタンが見つかりません。")
                await page.screenshot(path="logs/screenshots/coconala_error_no_applied_btn.png")
            
            return False
        except Exception as e:
            app_logger.error(f"[-] 返信プロセス中にエラー: {e}")
            return False
        finally:
            await browser.close()

async def reply_lancers(job_url, result_url):
    # 今後実装
    app_logger.info("[*] ランサーズ返信は現在準備中です。")
    return False

async def reply_crowdworks(job_url, result_url):
    # 今後実装
    app_logger.info("[*] クラウドワークス返信は現在準備中です。")
    return False

async def run_notifier():
    # スプレッドシートから最新の成果物を取得
    gc = gspread.service_account(filename="credentials.json")
    sh = gc.open_by_key(SPREADSHEET_ID)
    sheet = sh.get_worksheet(0)
    records = sheet.get_all_records()
    
    # statusが 'delivered' かつ 'result_url' があり、
    # かつ 'platform_replied' が未完了のものを探す
    for i, row in enumerate(records, start=2):
        status = str(row.get("__flow_status__", "")).lower()
        result_url = str(row.get("result_url", ""))
        job_url = str(row.get("job_url", ""))
        replied = str(row.get("platform_replied", "")).lower()
        
        if status in ["delivered", "done"] and result_url.startswith("http") and job_url.startswith("http") and replied != "done":
            success = await reply_to_platform(job_url, result_url)
            if success:
                # 返信済みフラグを立てる
                # まずヘッダーから platform_replied 列を探す
                headers = sheet.row_values(1)
                if "platform_replied" not in headers:
                    sheet.update_cell(1, len(headers) + 1, "platform_replied")
                    col_idx = len(headers) + 1
                else:
                    col_idx = headers.index("platform_replied") + 1
                
                sheet.update_cell(i, col_idx, "done")
                app_logger.info(f"✅ 返信完了フラグを更新しました: 行 {i}")

if __name__ == "__main__":
    asyncio.run(run_notifier())
