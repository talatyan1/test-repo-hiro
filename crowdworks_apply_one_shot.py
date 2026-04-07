
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
        # クラウドワークスのログイン状態を読み込み
        state_file = r"c:\Users\nagas\.gemini\antigravity\Hiro\crowd_agent\src\crawlers\state_crowdworks.json"
        if os.path.exists(state_file):
            context = await browser.new_context(storage_state=state_file)
        else:
            context = await browser.new_context()
        
        page = await context.new_page()
        # 応募画面
        job_url = "https://crowdworks.jp/proposals/new?job_offer_id=13034960"
        
        try:
            app_logger.info(f"[*] クラウドワークス一括応募開始: {job_url}")
            await page.goto(job_url)
            await asyncio.sleep(5)
            
            # --- 契約金額セクション ---
            # クラウドワークスの金額入力欄 (支払い方式の選択なども含む)
            # 1. 契約金額 (基本金額)
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
                "https://docs.google.com/forms/d/e/1FAIpQLSdZPLnDSEYgoccPig3lS6IVJx6R0G38NN0pSqc_sn-Uqd4Txw/viewform?usp=header\n\n"
                "まずは試作品をご覧いただき、そこから理想のサイトを一緒に作り上げられればと存じます。何卒よろしくお願い申し上げます。"
            )
            message_textarea = page.locator('textarea[name="proposal[body]"], textarea#proposal_body').first
            if await message_textarea.count() > 0:
                await message_textarea.fill(pr_text)
            
            app_logger.info("[*] フォーム入力完了。確認画面へ進みます...")
            await asyncio.sleep(2)
            
            # 確認画面へ進むボタン
            # 通常、下部にある「応募する」「確認する」ボタン
            confirm_btn = page.locator('input[type="submit"][value="応募する"], button:has-text("確認する")').first
            await confirm_btn.click()
            await asyncio.sleep(4)
            
            # もし、最終確定ボタンが必要な場合 (確認画面が表示されたら)
            # ページタイトルや要素をチェックして、最終送信を行う
            submit_btn = page.locator('input[type="submit"][value="応募する"], button:has-text("この内容で応募する")').first
            if await submit_btn.count() > 0:
                app_logger.info("[*] 最終確定ボタンをクリックします...")
                await submit_btn.click()
                await asyncio.sleep(5)
                await page.screenshot(path="crowdworks_spa_success.png")
                app_logger.info("[!] クラウドワークス応募完了！")
            
        except Exception as e:
            app_logger.error(f"[!] エラーが発生しました: {e}")
        finally:
            # 状況確認のため、ブラウザは維持
            pass

if __name__ == "__main__":
    asyncio.run(run())
