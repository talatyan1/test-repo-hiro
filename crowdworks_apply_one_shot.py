import asyncio
import os
import sys
from playwright.async_api import async_playwright

# パス追加
sys.path.append(os.getcwd())
try:
    from src.logger import app_logger
except ImportError:
    # 互換性のためのダミー
    import logging
    app_logger = logging.getLogger("crowd_agent")

async def js_click_with_retry(page, selector, label="ボタン", max_retries=3):
    """
    JSによるクリック、スクロール、およびリトライを組み合わせて
    確実にボタンをクリックするためのヘルパー関数です。
    """
    for i in range(max_retries):
        try:
            app_logger.info(f"[*] {label} のクリックを試行中... ({i+1}/{max_retries})")
            
            # 1. 存在確認とクリック可能まで待機
            element = page.locator(selector).first
            await element.wait_for(state="visible", timeout=10000)
            
            # 2. スクロール (人間と同じ操作を再現)
            handle = await element.element_handle()
            if handle:
                await page.evaluate("el => el.scrollIntoView({ behavior: 'smooth', block: 'center' })", handle)
                await asyncio.sleep(1) # スクロール後の安定化
                
                # 3. JSクリック (通常の click() が失敗する場合の保険)
                await page.evaluate("el => el.click()", handle)
                
                app_logger.info(f"✅ {label} をJSクリックしました。")
                return True
            else:
                app_logger.warning(f"⚠ {label} の要素ハンドル取得に失敗しました。")
        except Exception as e:
            app_logger.warning(f"⚠ {label} のクリックに失敗しました: {e}")
            await asyncio.sleep(2)
    return False

async def run():
    async with async_playwright() as p:
        # ヘッドレスモードをオフにしてUI挙動を確認 (100%確実な操作のため)
        browser = await p.chromium.launch(headless=False)
        
        state_file = r"c:\Users\nagas\.gemini\antigravity\Hiro\crowd_agent\src\crawlers\state_crowdworks.json"
        if os.path.exists(state_file):
            context = await browser.new_context(storage_state=state_file)
        else:
            context = await browser.new_context()
        
        page = await context.new_page()
        # 応募画面
        job_url = "https://crowdworks.jp/proposals/new?job_offer_id=13034960"
        
        try:
            app_logger.info(f"[*] クラウドワークス応募開始: {job_url}")
            # domcontentloaded で待機を打ち切り、要素があれば処理を開始するように高速化
            await page.goto(job_url, wait_until="domcontentloaded")
            
            # --- 初期アクセス時の成功判定 (既に応募済み・リダイレクトの場合など) ---
            # ページ内容もチェックして「応募済み」メッセージが出ていないか確認
            page_text = await page.content()
            success_indicators = ["complete", "applied", "messages", "contracts"]
            if any(k in page.url for k in success_indicators) or "すでに相談または応募" in page_text:
                app_logger.info(f"✅ 既に応募済み、または完了ページを検知しました。終了します。 (URL: {page.url})")
                await page.screenshot(path="crowdworks_spa_already_done.png")
                return # 正常終了

            # 通信が安定するまで少しだけ待つ
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except:
                pass

            # --- 契約金額セクション ---
            amount_input = page.locator('input[name="proposal[budget]"], input#proposal_budget').first
            if await amount_input.count() > 0:
                await amount_input.fill("250000")
            
            # --- 提案メッセージセクション ---
            pr_text = (
                "はじめまして。石川県野々市市でのタイ古式スパの新規オープン、誠におめでとうございます！\n\n"
                "募集記事を拝見し、「何者でもない自分に戻る余白」「脳の休息」という非常に洗練された素晴らしいコンセプトに深く感銘を受けました。"
                "30〜50代の働く女性や経営層という、日々多忙を極める方々に対し、心からの安らぎを提供するというクライアント様の想いを、"
                "制作・広告運用の面から全力でバックアップさせていただきたいと考えております。\n\n"
                "私は美容系LP制作の実績に加え、Meta広告（Instagram）の運用経験も豊富です。"
                "また、補助金を活用したプロジェクトにおける事務的なサポート（見積書や報告書の作成協力等）についても柔軟に対応可能です。\n\n"
                "お客様の想いを視覚化し、確実に来店に繋がるシステムを構築させていただきます。\n\n"
                "まずは、本案件のコンセプトに基づいた「試作品（プロトタイプ）」を早急にお届けいたします。\n"
                "以下の管理用フォームより、理想のイメージや特に大切にしたいポイントを簡単にお知らせください。\n"
                "https://forms.gle/...\n\n"
                "まずは試作品をご覧いただき、そこから理想のサイトを一緒に作り上げられればと存じます。何卒よろしくお願い申し上げます。"
            )
            message_textarea = page.locator('textarea[name="proposal[body]"], textarea#proposal_body').first
            if await message_textarea.count() > 0:
                await message_textarea.fill(pr_text)
            
            app_logger.info("[*] フォーム入力完了。確認画面へ進みます...")
            await asyncio.sleep(2)
            
            # ステップ1: 確認画面へ進む（または直接応募）ボタン
            confirm_selector = 'input[type="submit"][value="応募する"], input[type="submit"][value="内容を確認する"], button:has-text("確認する")'
            if await js_click_with_retry(page, confirm_selector, label="確認画面ボタン"):
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(3)
                
                # --- 即完了の判定 (追加) ---
                # 案件によっては確認画面がなく、直接応募が完了してメッセージルームへ飛ぶ場合がある
                current_url = page.url
                page_text = await page.content()
                
                if any(k in current_url for k in success_indicators) or "応募を完了しました" in page_text or "メッセージを投稿する" in page_text:
                    app_logger.info(f"✅ クラウドワークス応募完了！ (直接遷移/メッセージ画面検知: {current_url})")
                    await page.screenshot(path="crowdworks_spa_success_direct.png")
                    return # 正常終了
                
                # ステップ2: 最終確定ボタン (確認画面に遷移した場合のみ)
                final_selector = 'input[type="submit"][value="応募する"], button:has-text("この内容で応募する")'
                # 確認画面かどうかを判定
                if await page.locator(final_selector).count() > 0:
                    app_logger.info("[*] 最終確認画面を検知。確定ボタンを押します...")
                    if await js_click_with_retry(page, final_selector, label="最終応募ボタン"):
                        await page.wait_for_load_state("networkidle")
                        await asyncio.sleep(5)
                
                # 最終的な成功判定
                current_url = page.url
                page_text = await page.content()
                if any(k in current_url for k in success_indicators) or "応募を完了しました" in page_text or "メッセージを投稿する" in page_text:
                    app_logger.info(f"✅ クラウドワークス応募完了！ (最終URL: {current_url})")
                    await page.screenshot(path="crowdworks_spa_success_final.png")
                else:
                    app_logger.error(f"❌ 応募完了の確証が得られませんでした。URL: {current_url}")
                    await page.screenshot(path="crowdworks_spa_fail_check.png")
            else:
                app_logger.error("❌ 確認ボタンのクリックに失敗しました。")

        except Exception as e:
            app_logger.error(f"[!] 致命的なエラーが発生しました: {e}")
            await page.screenshot(path="crowdworks_spa_fatal_error.png")
        finally:
            # 状況確認のため、ブラウザ維持または待機
            await asyncio.sleep(5)
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
