
import asyncio
import os
import sys
import json
from playwright.async_api import async_playwright

# パス追加
sys.path.append(os.getcwd())
from src.logger import app_logger

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        # ログイン状態のステートを読み込み
        state_file = r"c:\Users\nagas\.gemini\antigravity\Hiro\crowd_agent\src\crawlers\state_lancers.json"
        if os.path.exists(state_file):
            context = await browser.new_context(storage_state=state_file)
        else:
            context = await browser.new_context()
        
        page = await context.new_page()
        job_url = "https://www.lancers.jp/work/propose/5520604"
        
        try:
            app_logger.info(f"[*] ランサーズ一括応募開始: {job_url}")
            await page.goto(job_url)
            await asyncio.sleep(4)
            
            # --- 入力セクション ---
            # タイトル (日付なし)
            title_input = page.locator('input[name="data[Proposal][title]"]').first
            if await title_input.count() > 0:
                await title_input.fill("アクセサリー・貴金属のウェブサイト作成のご提案")
            
            # 完了予定日 (5日後: 2026/04/08)
            date_input = page.locator('input[name="data[Proposal][plan_at]"]').first
            if await date_input.count() > 0:
                await date_input.fill("2026/04/08")
            
            # 契約金額 (50,000)
            amount_input = page.locator('input[name="data[Proposal][planned_amount]"]').first
            if await amount_input.count() > 0:
                await amount_input.fill("50000")
            
            # 自己PR
            pr_text = (
                "アクセサリー・貴金属のリユースサイト制作、非常に魅力的なプロジェクトですね。\n"
                "商品の高級感や信頼性を引き立たせ、かつリユース業特有の「安心感」をユーザーに与えるデザインをご提案させていただきます。\n\n"
                "詳細なイメージをお聞かせいただければ、すぐに実際のウェブページの試作品（プロトタイプ）を作成してお届けいたします。\n"
                "まずはこちらのフォームより、お客様の理想とするイメージやご要望を簡単にお知らせください。\n"
                "https://docs.google.com/forms/d/e/1FAIpQLSdZPLnDSEYgoccPig3lS6IVJx6R0G38NN0pSqc_sn-Uqd4Txw/viewform?usp=header\n\n"
                "まずは試作品をご覧いただき、そこから理想のサイトを一緒に作り上げられればと存じます。何卒よろしくお願い申し上げます。"
            )
            desc_textarea = page.locator('textarea[name="data[Proposal][description]"]').first
            if await desc_textarea.count() > 0:
                await desc_textarea.fill(pr_text)
            
            # AI宣言 (使用しない)
            ai_no = page.locator('input[name*="ai_declaration"][value="0"]').first
            if await ai_no.count() > 0:
                await ai_no.click()
            
            app_logger.info("[*] フォーム入力完了。確認画面へ進みます...")
            await asyncio.sleep(2)
            
            # 内容を確認するボタン (青または緑の大きなボタン)
            confirm_btn = page.locator('button:has-text("内容を確認する"), input[value="内容を確認する"]').first
            if await confirm_btn.count() > 0:
                await confirm_btn.click()
                await asyncio.sleep(4)
                
                # 最終確定ボタン (確認画面)
                final_btn = page.locator('button:has-text("提案する"), button:has-text("利用規約に同意して提案する")').first
                if await final_btn.count() > 0:
                    app_logger.info("[*] 最終確定ボタンをクリックします...")
                    await final_btn.click()
                    await asyncio.sleep(5)
                    await page.screenshot(path="lancers_reuse_success.png")
                    app_logger.info("[!] 応募が完了しました！")
            
        except Exception as e:
            app_logger.error(f"[!] エラーが発生しました: {e}")
        finally:
            # ユーザーが結果を確認できるようブラウザは開き続ける
            pass

if __name__ == "__main__":
    asyncio.run(run())
