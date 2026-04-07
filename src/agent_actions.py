import asyncio
from src.crawlers.base import BaseCrawler
from src.logger import app_logger, error_logger

class AgentActions:
    def __init__(self, headless: bool = True):
        self.headless = headless
        from src.ui_resolver import UIResolver
        self.healer = UIResolver()

    async def apply_to_crowdworks(self, job_url: str, proposal_text: str, reward: str = "10000"):
        """
        クラウドワークスの案件に応募します。
        """
        from playwright.async_api import async_playwright
        import os

        state_file = "src/crawlers/state_crowdworks.json"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            
            # ログイン状態の復元
            if os.path.exists(state_file):
                context = await browser.new_context(storage_state=state_file)
            else:
                app_logger.error("応募に失敗: ログイン状態が見つかりません。先に refresh_sessions.py を実行してください。")
                await browser.close()
                return False, "ログイン状態ファイルが見つかりません。"

            page = await context.new_page()
            # スクリーンショット用ディレクトリ
            shot_dir = "logs/screenshots"
            os.makedirs(shot_dir, exist_ok=True)
            try:
                job_id = job_url.split("/")[-1]
            except:
                job_id = "unknown"
            
            try:
                app_logger.info(f"[*] 応募ページへ遷移中: {job_url}")
                await page.goto(job_url)
                await page.wait_for_load_state("networkidle")
                await page.screenshot(path=f"{shot_dir}/cw_{job_id}_1_start.png")
                
                # 「応募する」ボタンをクリック (ログイン状態によりセレクタが変動する可能性あり)
                apply_button = page.get_by_text("応募する", exact=True).first
                if await apply_button.count() == 0:
                    apply_button = page.get_by_role("button", name="応募する").first
                
                if await apply_button.count() == 0:
                    # 既にボタンがない場合（募集終了や応募済み）
                    if not await self._is_logged_in_crowdworks(page):
                        app_logger.error(f"クラウドワークス応募失敗: セッション切れ: {job_url}")
                        return False, "セッション切れ（要再ログイン）"
                    
                    app_logger.warning(f"「応募する」ボタンが見つかりません。募集終了の可能性があります: {job_url}")
                    return False, "応募ボタン不在（募集終了？）"
                
                await apply_button.click()
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)
                await page.screenshot(path=f"{shot_dir}/cw_{job_id}_2_form.png")

                # --- 応募フォーム入力 ---
                # 1. 契約金額 (税抜)
                # 可視状態の入力欄を探す
                amount_input = page.locator('input[name="proposal[amount]"]:visible, input#proposal_amount:visible').first
                if await amount_input.count() > 0:
                    import re
                    clean_reward = re.sub(r'[^\d]', '', reward)
                    if not clean_reward: clean_reward = "10000"
                    await amount_input.scroll_into_view_if_needed()
                    await amount_input.fill(clean_reward)
                
                # 2. メッセージ (提案文)
                message_textarea = page.locator('textarea[name="proposal[body]"]')
                if await message_textarea.count() > 0:
                    await message_textarea.fill(proposal_text)
                else:
                    return False, "メッセージ入力欄が見つかりません"
                
                # 3. 利用規約・NDAへの同意 (もしあれば)
                await self._handle_nda_and_consent(page)
                
                # 4. 確認画面へ
                confirm_button = page.get_by_text("内容を確認する", exact=True).first
                if await confirm_button.count() == 0:
                    confirm_button = page.locator('input[type="submit"][value*="確認"]').first
                
                if await confirm_button.count() > 0:
                    await confirm_button.click()
                    await page.wait_for_load_state("networkidle")
                    await page.screenshot(path=f"{shot_dir}/cw_{job_id}_3_confirm.png")
                    
                    # 最終的な「応募する」
                    final_submit = page.locator('input[type="submit"][value="応募する"]').first
                    if await final_submit.count() > 0:
                        app_logger.info("[!] 最終的な応募ボタンをクリックします。")
                        await final_submit.click()
                        await page.wait_for_load_state("networkidle")
                        await asyncio.sleep(3)
                        
                        # 成功判定: URLに 'complete' が含まれる、または「応募を完了しました」という文字がある
                        success_indicators = ["complete", "applied"]
                        if any(k in page.url for k in success_indicators) or await page.get_by_text("応募を完了しました").count() > 0 or await page.get_by_text("応募履歴").count() > 0:
                            app_logger.info(f"✅ 応募完了しました: {job_url}")
                            await page.screenshot(path=f"{shot_dir}/cw_{job_id}_4_success.png")
                            return True, "成功"
                        else:
                            app_logger.warning(f"応募ボタン押下後、成功画面への遷移が確認できませんでした: {page.url}")
                            await page.screenshot(path=f"{shot_dir}/cw_{job_id}_4_success_check_failed.png")
                            return False, "完了画面への遷移失敗"
                    else:
                        return False, "最終確認画面で応募ボタンが見つかりません"
                else:
                    # 直接応募ボタンの場合
                    direct_submit = page.locator('input[type="submit"][value="応募する"]').first
                    if await direct_submit.count() > 0:
                        await direct_submit.click()
                        await page.wait_for_load_state("networkidle")
                        if "complete" in page.url or await page.get_by_text("応募を完了しました").count() > 0:
                            app_logger.info(f"✅ 応募完了しました（直接）: {job_url}")
                            return True, "成功（直接）"
                    
                return False, "応募フォーム送信失敗"

            except Exception as e:
                error_logger.error(f"応募中にエラー発生: {e}")
                await page.screenshot(path=f"{shot_dir}/cw_{job_id}_error.png")
                return False, f"システムエラー: {str(e)}"
            finally:
                await browser.close()

    async def apply_to_lancers(self, job_url: str, proposal_text: str, reward: str = "10000"):
        """
        ランサーズの案件に提案します。
        """
        from playwright.async_api import async_playwright
        import os
        import re

        state_file = "src/crawlers/state_lancers.json"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            
            if os.path.exists(state_file):
                context = await browser.new_context(storage_state=state_file)
            else:
                app_logger.error("ランサーズ応募失敗: ログイン状態が見つかりません。")
                await browser.close()
                return False, "ログイン状態ファイルが見つかりません"

            page = await context.new_page()
            shot_dir = "logs/screenshots"
            os.makedirs(shot_dir, exist_ok=True)
            try:
                job_id = job_url.split("/")[-1]
            except:
                job_id = "unknown"
            
            try:
                app_logger.info(f"[*] ランサーズ案件ページへ遷移中: {job_url}")
                await page.goto(job_url)
                await asyncio.sleep(3)
                await page.screenshot(path=f"{shot_dir}/ls_{job_id}_1_start.png")

                # ログイン状態の最終点検 (未ログインならセッションを復旧)
                login_btn = page.locator('a[href*="/user/login"], .c-nav-main__link--login').first
                if await login_btn.count() > 0 and await login_btn.is_visible():
                    app_logger.warning("[!] ランサーズ: 詳細ページで未ログインを検知。セッションを復旧します...")
                    storage_state = "src/crawlers/state_lancers.json"
                    if os.path.exists(storage_state):
                        import json
                        with open(storage_state, "r") as f:
                            state = json.load(f)
                            await page.context.add_cookies(state["cookies"])
                        await page.reload()
                        await asyncio.sleep(3)
                    else:
                        app_logger.error("[!] ランサーズ: セッションファイルが見つからないため、ログイン不可です。")

                # 募集終了チェック (即座にスキップ)
                closed_indicator = page.locator('text="募集終了", text="受付終了", text="掲載終了", text="提案の受付は終了"').first
                if await closed_indicator.count() > 0:
                    app_logger.warning(f"[!] ランサーズ: 募集終了または受付終了のためスキップします: {job_url}")
                    return False, "募集終了"

                # 「提案する」または「ログインして提案する」ボタンを探す (セレクタを強化)
                proposal_button = page.locator('a.p-work-detail__righter-button:has-text("提案する"), a.p-work-detail__floating-footer-button:has-text("提案する"), button:has-text("提案する")').first
                if await proposal_button.count() == 0:
                    proposal_button = page.get_by_text("提案する").first
                
                if await proposal_button.count() == 0:
                    if not await self._is_logged_in_lancers(page):
                        app_logger.error(f"ランサーズ応募失敗: セッション切れ: {job_url}")
                        return False, "セッション切れ（要再ログイン）"

                    app_logger.warning(f"Lancers: 提案ボタンが見つかりません。既に応募済みか期限切れの可能性があります: {job_url}")
                    return False, "提案ボタン不在"
                else:
                    await proposal_button.click()

                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)
                await page.screenshot(path=f"{shot_dir}/ls_{job_id}_2_form.png")

                # --- 提案フォーム入力 ---
                # 1. 金額 (税抜)
                # 可視状態の入力欄を優先。Lancersではマイルストーンのhiddenフィールドが先にヒットするため。
                price_input = page.locator('input[type="number"]:visible, input[id*="AmountExcludeTax"]:visible, input[name*="[amount_exclude_tax]"]:visible').first
                if await price_input.count() > 0:
                    clean_reward = re.sub(r'[^\d]', '', reward)
                    if not clean_reward: clean_reward = "10000"
                    await price_input.scroll_into_view_if_needed()
                    await price_input.fill(clean_reward)
                
                # 2. 提案文
                desc_textarea = page.locator('textarea[id*="ProposalDescription"], textarea[name*="[description]"]').first
                if await desc_textarea.count() > 0:
                    await desc_textarea.fill(proposal_text)
                
                # 完了予定日の入力を強化（バリデーション発火のため、クリックとTabを組み合わせる）
                import datetime
                target_date = (datetime.datetime.now() + datetime.timedelta(days=14)).strftime("%Y/%m/%d")
                
                # タイトルの特定（「プロジェクトの完成」などが入っている場所）
                title_input = page.locator('input[name*="[title]"]').first

                date_input = page.locator('input[placeholder*="年 / 月 / 日"], input[name*="[plan_at]"]').first
                if await date_input.count() > 0:
                    await date_input.click()
                    await date_input.fill("") # 一度空にする
                    await date_input.type(target_date, delay=50) # 1文字ずつ入力して確実に認識させる
                    await date_input.press("Tab")
                    # 別の要素（タイトルなど）をクリックして、フォーカスアウトによるバリデーションを発動させる
                    if await title_input.count() > 0:
                        await title_input.click()
                    app_logger.info(f"完了予定日をセットしました: {target_date}")
                
                # 3. AI宣言 (ラベルをクリックして確実に選択)
                ai_label = page.locator('label:has(input[name*="ai_declaration"][value="0"])').first
                if await ai_label.count() > 0:
                    await ai_label.click()
                else:
                    ai_radio = page.locator('input[name*="ai_declaration"][value="0"]').first
                    if await ai_radio.count() > 0:
                        await ai_radio.check(force=True)

                # 4. 同意チェック・NDA (あれば)
                await self._handle_nda_and_consent(page)

                # 5. 確認画面へ
                submit_btn = page.get_by_text("内容を確認する", exact=True).first
                if await submit_btn.count() == 0:
                    submit_btn = page.locator('.js-proposal-submit, button[type="submit"]').first
                
                if await submit_btn.count() > 0:
                    await submit_btn.click()
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(2)
                    await page.screenshot(path=f"{shot_dir}/ls_{job_id}_3_confirm.png")
                    
                    # 最終送信
                    final_btn = page.get_by_role("button", name="提案する").first
                    if await final_btn.count() == 0:
                        final_btn = page.locator('input[type="submit"][value*="同意して提案"], button:has-text("同意して提案"), #form_end').first
                    
                    if await final_btn.count() > 0:
                        app_logger.info("[!] ランサーズ確定ボタン（同意して提案）を特定しました。")
                        await final_btn.scroll_into_view_if_needed()
                        
                        # 最終確認画面の規約等（もしあれば）をチェック
                        agree_check = page.locator('input[type="checkbox"][name*="agree"], .c-checkbox:has-text("同意")').first
                        if await agree_check.count() > 0:
                            try:
                                await agree_check.check()
                            except:
                                await agree_check.click()
                        
                        # 完全自動化：ユーザー確認をスキップし、即座にクリックします。
                        try:
                            await final_btn.click()
                        except:
                            pass

                        await asyncio.sleep(2)
                        
                        # 成功判定 (メッセージとURL両方でチェック、さらに緩和)
                        success_texts = [
                            "提案を完了しました", 
                            "内容を送信しました", 
                            "依頼への提案が完了しました",
                            "提案履歴",
                            "提案一覧"
                        ]
                        has_success_text = False
                        for t in success_texts:
                            if await page.get_by_text(t).count() > 0:
                                has_success_text = True
                                break

                        if has_success_text or any(k in page.url for k in ["finish", "complete", "propose_success", "proposal/index"]):
                            app_logger.info(f"✅ ランサーズ応募完了: {job_url}")
                            await page.screenshot(path=f"{shot_dir}/ls_{job_id}_4_success.png")
                            return True, "成功"
                        else:
                            # 既に提案済みの場合は成功扱いにする
                            if await page.get_by_text("提案済み").count() > 0 or await page.get_by_text("提案を編集する").count() > 0:
                                app_logger.info(f"✅ ランサーズ: 既に提案済みのため成功扱いにします: {job_url}")
                                return True, "既に提案済み"
                            
                            return False, f"完了画面判定失敗 (URL: {page.url})"
                
                return False, "提案フォーム送信失敗"

            except Exception as e:
                error_logger.error(f"ランサーズ応募中にエラー: {e}")
                await page.screenshot(path=f"{shot_dir}/ls_{job_id}_error.png")
                return False, f"システムエラー: {str(e)}"
            finally:
                await browser.close()


    async def apply_to_coconala(self, job_url: str, proposal_text: str, reward: str = "10000"):
        """
        ココナラの公募（仕事・相談）に対して「提案」または「見積り提案」を行います。
        """
        from playwright.async_api import async_playwright
        import os

        state_file = "src/crawlers/state_coconala.json"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            
            if os.path.exists(state_file):
                context = await browser.new_context(storage_state=state_file)
            else:
                app_logger.error("ココナラ応募失敗: ログイン状態が見つかりません。")
                await browser.close()
                return False, "ログイン状態ファイルが見つかりません"

            page = await context.new_page()
            shot_dir = "logs/screenshots"
            os.makedirs(shot_dir, exist_ok=True)
            try:
                job_id = job_url.split("/")[-1]
            except:
                job_id = "unknown"
            
            try:
                app_logger.info(f"[*] ココナラ案件ページへ遷移中: {job_url}")
                await page.goto(job_url)
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(3)
                await page.screenshot(path=f"{shot_dir}/cn_{job_id}_1_start.png")

                # 「提案を入力する」または「見積り提案を入力する」ボタンを探す
                proposal_btn = page.get_by_text("提案を入力する").first
                if await proposal_btn.count() == 0:
                    proposal_btn = page.get_by_text("見積り提案を入力する").first
                
                if await proposal_btn.count() == 0:
                    if not await self._is_logged_in_coconala(page):
                        app_logger.error(f"ココナラ応募失敗: セッション切れ: {job_url}")
                        return False, "セッション切れ（要再ログイン）"

                    app_logger.warning(f"ココナラの募集ボタンが見つかりません: {job_url}")
                    return False, "提案ボタン不在"
                else:
                    await proposal_btn.click()

                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(2)
                await page.screenshot(path=f"{shot_dir}/cn_{job_id}_2_form.png")

                # --- 提案フォーム入力 ---
                # 1. 提案内容・メッセージ
                message_area = page.locator('textarea[name*="comment"], textarea[id*="comment"]').first
                if await message_area.count() > 0:
                    await message_area.fill(proposal_text)
                
                # 2. 金額 (あれば)
                price_area = page.locator('input[name*="price"]:visible, input[id*="price"]:visible').first
                if await price_area.count() > 0:
                    import re
                    clean_reward = re.sub(r'[^\d]', '', reward)
                    if not clean_reward: clean_reward = "5000"
                    await price_area.scroll_into_view_if_needed()
                    await price_area.fill(clean_reward)

                # 3. 同意チェック・NDA (あれば)
                await self._handle_nda_and_consent(page)

                # 3. 確認画面・送信
                confirm_btn = page.get_by_role("button", name="確認画面へ進む").first
                if await confirm_btn.count() == 0:
                    confirm_btn = page.get_by_text("内容を確認する").first
                
                if await confirm_btn.count() > 0:
                    await confirm_btn.click()
                    await page.wait_for_load_state("domcontentloaded")
                    await asyncio.sleep(2)
                    await page.screenshot(path=f"{shot_dir}/cn_{job_id}_3_confirm.png")
                    
                    # 最終送信
                    submit_btn = page.get_by_role("button", name="提案を送信する").first
                    if await submit_btn.count() == 0:
                        submit_btn = page.get_by_text("送信する").last
                        
                    if await submit_btn.count() > 0:
                        app_logger.info("[!] ココナラ最終送信ボタンをクリックします。")
                        await submit_btn.click()
                        await page.wait_for_load_state("networkidle")
                        await asyncio.sleep(3)
                        
                        # 成功判定
                        if await page.get_by_text("提案を送信しました").count() > 0 or "complete" in page.url:
                            app_logger.info(f"✅ ココナラ応募完了: {job_url}")
                            await page.screenshot(path=f"{shot_dir}/cn_{job_id}_4_success.png")
                            return True, "成功"
                        else:
                            app_logger.warning(f"ココナラ完了画面への遷移が確認できませんでした: {page.url}")
                            await page.screenshot(path=f"{shot_dir}/cn_{job_id}_4_success_check_failed.png")
                            return False, "完了画面への遷移失敗"
                
                return False, "提案フォーム送信失敗"

            except Exception as e:
                error_logger.error(f"ココナラ応募中にエラー: {e}")
                await page.screenshot(path=f"{shot_dir}/cn_{job_id}_error.png")
                return False, f"システムエラー: {str(e)}"
            finally:
                await browser.close()
    async def _is_logged_in_crowdworks(self, page) -> bool:
        """クラウドワークスのログイン状態を確認します。"""
        try:
            # ログアウトボタンまたはマイページへのリンクがあるか確認
            selectors = [
                'a[href*="/dashboard"]',
                'a:has-text("ログアウト")',
                '.navbar-user'
            ]
            for s in selectors:
                if await page.locator(s).count() > 0:
                    return True
            return False
        except:
            return False

    async def _is_logged_in_lancers(self, page) -> bool:
        """ランサーズのログイン状態を確認します。"""
        try:
            # ログインボタンが表示されている場合は未ログイン
            login_btn = page.locator('a[href*="/user/login"], .c-nav-main__link--login').first
            if await login_btn.count() > 0 and await login_btn.is_visible():
                return False
            
            # ユーザーアイコンやマイページリンクがあるか確認
            selectors = [
                '.c-user-nav',
                'a[href*="/mypage"]',
                '.c-header__info'
            ]
            for s in selectors:
                if await page.locator(s).count() > 0:
                    return True
            return False
        except:
            return False

    async def _is_logged_in_coconala(self, page) -> bool:
        """ココナラのログイン状態を確認します。"""
        try:
            # ログインボタンがあるか確認
            login_btn = page.locator('a[href*="/login"]').first
            if await login_btn.count() > 0 and await login_btn.is_visible():
                return False
            
            # 出品者メニューや通知などがあるか確認
            selectors = [
                '.c-headerUserNav',
                'a[href*="/mypage"]'
            ]
            for s in selectors:
                if await page.locator(s).count() > 0:
                    return True
            return False
        except:
            return False

    async def _handle_nda_and_consent(self, page):
        """
        ページ内の「秘密保持」「NDA」「同意」「承諾」に関連するチェックボックスを自動でオンにします。
        """
        try:
            # 1. 露骨なNDA関連のチェック
            nda_selectors = [
                 'label:has-text("秘密保持")',
                 'label:has-text("NDA")',
                 'input[type="checkbox"][name*="nda"]',
                 'input[type="checkbox"][id*="nda"]'
            ]
            for s in nda_selectors:
                elements = page.locator(s)
                count = await elements.count()
                for i in range(count):
                    el = elements.nth(i)
                    if await el.is_visible():
                        app_logger.info(f"[NDA] 秘密保持・NDA関連のチェックを検知し、同意します: {s}")
                        # labelの場合はクリック、checkboxの場合はcheckを試みる
                        try:
                            if await el.get_attribute("type") == "checkbox":
                                await el.check()
                            else:
                                await el.click()
                        except:
                            await el.click()

            # 2. 一般的な「同意」「承諾」「利用規約」チェック
            consent_selectors = [
                'label:has-text("同意")',
                'label:has-text("承諾")',
                'label:has-text("利用規約")',
                'input[type="checkbox"][name*="agree"]',
                'input[type="checkbox"][name*="consent"]'
            ]
            for s in consent_selectors:
                elements = page.locator(s)
                count = await elements.count()
                for i in range(count):
                    el = elements.nth(i)
                    if await el.is_visible():
                        # すでにチェックされているかチェック
                        is_checked = False
                        try:
                            # label の中に checkbox があるパターンも考慮
                            cb = el.locator('input[type="checkbox"]')
                            if await cb.count() > 0:
                                is_checked = await cb.is_checked()
                            else:
                                is_checked = await el.is_checked()
                        except:
                            pass

                        if not is_checked:
                            app_logger.info(f"[CONSENT] 同意・承諾関連のチェックを検知し、同意します: {s}")
                            try:
                                await el.click()
                            except:
                                # ボタン（label）がチェックボックスを覆っている場合があるので、とにかくクリック
                                await el.click()
        except Exception as e:
            app_logger.warning(f"NDA/同意チェック処理中に軽微なエラー（スキップします）: {e}")
