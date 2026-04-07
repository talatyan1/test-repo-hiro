
import asyncio
import os
import sys
from playwright.async_api import async_playwright

# パス追加
sys.path.append(os.getcwd())
from src.logger import app_logger

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        # ココナラのログイン状態を読み込み
        state_file = r"c:\Users\nagas\.gemini\antigravity\Hiro\crowd_agent\src\crawlers\state_coconala.json"
        if os.path.exists(state_file):
            context = await browser.new_context(storage_state=state_file)
        else:
            context = await browser.new_context()
        
        page = await context.new_page()
        # 案件詳細ページ
        job_url = "https://coconala.com/requests/4942487"
        
        try:
            app_logger.info(f"[*] ココナラ一括応募開始: {job_url}")
            await page.goto(job_url)
            await asyncio.sleep(4)
            
            # 1. 受注者モードへの切替 (もし必要なら)
            # ヘッダーにある「受注者モードへ」ボタン
            mode_switch = page.locator('button:has-text("出品者モードに切替"), a:has-text("出品者モードに切替")').first
            if await mode_switch.count() > 0:
                app_logger.info("[*] 出品者モードへ切り替えます...")
                await mode_switch.click()
                await asyncio.sleep(2)
            
            # 2. 提案するボタンのクリック
            propose_btn = page.locator('a:has-text("提案する"), button:has-text("提案する")').first
            if await propose_btn.count() > 0:
                await propose_btn.click()
                await asyncio.sleep(4)
            
            # --- フォーム入力セクション ---
            # 3. 提案タイトル
            title_input = page.locator('input[name="title"], input#proposal_title').first
            if await title_input.count() > 0:
                await title_input.fill("比較サイトLP デザイン＆HTML/CSSコーディングのご提案")
            
            # 4. 提案内容 (メッセージ)
            pr_text = (
                "はじめまして。比較サイトの広告用LP制作案件、非常に興味深く拝見いたしました。\n"
                "比較サイトにおいては、多数の情報を整理し、ユーザーがいかに直感的にメリットを感じられるかというUI/UXの設計が成果の鍵となります。\n"
                "私は、HTML/CSS/JSを用いた純粋なコーディング技術を強みとしており、レスポンシブ対応はもちろん、軽量で表示速度の速い、成果に直結するLPを制作可能です。\n\n"
                "詳細な構成案やイメージをお聞かせいただければ、すぐに実際のウェブページの試作品（プロトタイプ）を作成してお届けいたします。\n"
                "まずはこちらのフォームより、お客様が特に重視したいポイントや競合他社のイメージなどを簡単にお知らせください。\n"
                "https://docs.google.com/forms/d/e/1FAIpQLSdZPLnDSEYgoccPig3lS6IVJx6R0G38NN0pSqc_sn-Uqd4Txw/viewform?usp=header\n\n"
                "まずは試作品をご覧いただき、そこから理想のサイトを一緒に作り上げられればと存じます。何卒よろしくお願い申し上げます。"
            )
            message_textarea = page.locator('textarea[name="message"], textarea#proposal_message, textarea[name="body"]').first
            if await message_textarea.count() > 0:
                await message_textarea.fill(pr_text)
            
            # 5. 提案金額
            amount_input = page.locator('input[name="price"], input[name="amount"]').first
            if await amount_input.count() > 0:
                await amount_input.fill("80000")
            
            # 6. 納品予定日 (2026/04/08)
            date_input = page.locator('input[name="delivery_date"], .flatpickr-input').first
            if await date_input.count() > 0:
                await date_input.fill("2026/04/08")
            
            app_logger.info("[*] フォーム入力完了。確認画面へ進みます...")
            await asyncio.sleep(2)
            
            # 7. 確認・応募ボタン
            submit_btn = page.locator('input[type="submit"][value="内容を確認する"], button:has-text("確認する")').first
            await submit_btn.click()
            await asyncio.sleep(4)
            
            # 最終的な「この内容で提案する」
            final_btn = page.locator('input[type="submit"][value="提案する"], button:has-text("この内容で提案する")').first
            if await final_btn.count() > 0:
                app_logger.info("[*] 最終提案ボタンをクリックします...")
                await final_btn.click()
                await asyncio.sleep(5)
                await page.screenshot(path="coconala_lp_success.png")
                app_logger.info("[!] ココナラ応募完了！")
            
        except Exception as e:
            app_logger.error(f"[!] エラーが発生しました: {e}")
        finally:
            # ブラウザは閉じない
            pass

if __name__ == "__main__":
    asyncio.run(run())
