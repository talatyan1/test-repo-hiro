import os
import sys
import time
import traceback
import gspread
import zipfile
import shutil
import re
from dotenv import load_dotenv

# .envファイルのロード
load_dotenv()

# SEO最適化モジュール等の読み込み
from seo_optimizer import optimize_website
from delivery_notifier import send_delivery_email

# Windows環境でのターミナル出力エラー(cp932)対策
sys.stdout.reconfigure(encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


# ===============================
# Google Sheets 設定
# ===============================
SPREADSHEET_ID = "1xALyErlbTB7P32gf8b4qq4JY70FYxnA7PPOiMvHIK6U"

def get_sheet():
    print("🟡 Google Sheets 接続開始...")
    gc = gspread.service_account(filename="credentials.json")
    print(f"🟡 ID: {SPREADSHEET_ID} をオープンします...")
    sh = gc.open_by_key(SPREADSHEET_ID)
    print("✅ スプレッドシートの取得に成功しました。")
    return sh.get_worksheet(0)


def find_col_index(headers, keywords):
    for i, h in enumerate(headers):
        h_str = str(h).lower().strip().replace(" ", "").replace("_", "")
        for kw in keywords:
            kw_clean = kw.lower().strip().replace(" ", "").replace("_", "")
            if kw_clean in h_str:
                return i + 1
    return -1

def get_new_jobs(sheet):
    print("🟡 案件一覧を取得しています...")
    headers = sheet.row_values(1)
    print(f"📊 シートのヘッダー: {headers}")
    records = sheet.get_all_records()
    print(f"📊 全レコード数: {len(records)}")
    jobs = []
    
    if not records: 
        print("💡 レコードが1件もありません。")
        return []

    for i, row in enumerate(records, start=2):
        status_val = str(row.get("__flow_status__", "")).strip().lower()
        legacy_status = str(row.get("status", "")).strip().lower()
        print(f"🔍 行 {i}: __flow_status__='{status_val}', status='{legacy_status}'")
        
        if status_val in ["done", "delivered", "error", "processing"] or \
           legacy_status in ["done", "delivered", "processing"]:
            continue
        has_content = any(str(v).strip() for k, v in row.items() if k not in ["__flow_status__", "status", "result_url", "__flow_site_url__"])
        if has_content:
            row["_row"] = i
            jobs.append(row)
        else:
            print(f"⚠️ 行 {i}: コンテンツが空と判定されました。 Keys: {list(row.keys())}")
    jobs.reverse()
    print(f"🚀 処理対象の新規案件: {len(jobs)} 件")
    return jobs

def update_status(sheet, row, status_val):
    headers = sheet.row_values(1)
    idx_legacy = find_col_index(headers, ["status", "ステータス", "状態"])
    idx_system = find_col_index(headers, ["__flow_status__"])
    if idx_system == -1:
        idx_system = len(headers) + 1
        sheet.update_cell(1, idx_system, "__flow_status__")
    if idx_system != -1:
        sheet.update_cell(row, idx_system, status_val)
    if idx_legacy != -1:
        sheet.update_cell(row, idx_legacy, status_val)

def update_result_url(sheet, row, url):
    if not url: return
    headers = sheet.row_values(1)
    col_idx = find_col_index(headers, ["__site_url__", "result_url", "公開URL"])
    if col_idx == -1:
        col_idx = len(headers) + 1
        sheet.update_cell(1, col_idx, "__site_url__")
    sheet.update_cell(row, col_idx, url)


# ===============================
# Selenium 起動
# ===============================
def start_driver():
    print(f"🟡 ブラウザを起動します (プロファイル: {r'C:\readdy_profile'})")
    options = Options()
    options.add_argument("--start-maximized")
    profile_path = r"C:\readdy_profile"
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_experimental_option("detach", True)
    
    download_dir = os.path.abspath("downloads")
    if not os.path.exists(download_dir): 
        os.makedirs(download_dir)
        print(f"📁 ダウンロードディレクトリを作成しました: {download_dir}")
        
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument('--disable-blink-features=AutomationControlled')
    
    driver = webdriver.Chrome(options=options)
    print("✅ Selenium ドライバの初期化が完了しました。")
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver


# ===============================
# Readdy 入力処理
# ===============================
def fill_readdy_form(driver, job):
    wait = WebDriverWait(driver, 20)
    print("🟡 Readdyフォーム入力開始")
    try:
        time.sleep(3)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "textarea, input")))
        
        # プロンプトの構築
        exclude_keys = ["timestamp", "status", "result_url", "_row", "email", "メールアドレス"]
        form_details = ""
        for k, v in job.items():
            if str(k).strip().lower() not in exclude_keys and v:
                form_details += f"【{str(k).strip()}】\n{v}\n\n"

        prompt_text = f"以下をもとにSEO・GEO・LLMOに最適化したWebサイトを生成してください。\n\n{form_details.strip()}"

        editables = driver.find_elements(By.CSS_SELECTOR, "[contenteditable='true'], [role='textbox']")
        if len(editables) >= 1:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", editables[0])
            time.sleep(1)
            actions = ActionChains(driver)
            actions.move_to_element(editables[0]).click().pause(0.5)
            # プロンプトを入力 (Shift+Enterで改行)
            for line in prompt_text.split("\n"):
                actions.send_keys(line).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)
            actions.send_keys(Keys.ENTER).perform()
            print("🟢 生成を開始します")
            return

        # Fallback
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        if textareas:
            textareas[0].send_keys(prompt_text)
            textareas[0].send_keys(Keys.ENTER)
            print("🟢 生成を開始します (textarea)")

    except Exception as e:
        print("❌ fill_readdy_form エラー:", e)
        raise e


# ===============================
# Readdy 生成画面以降の自動進行
# ===============================
def process_readdy_generation(driver, job):
    print("\n⏳ サイト生成自動制御 (ステップ進行)")
    # 次へボタン
    for _ in range(6): 
        time.sleep(5)
        btns = driver.find_elements(By.CSS_SELECTOR, "button, [role='button'], a")
        found = False
        for b in btns:
            try:
                t = b.text or ""
                if "次へ" in t or "Next" in t:
                    driver.execute_script("arguments[0].click();", b); found = True; break
            except: pass
        if found: break
            
    # ロゴ・最終生成
    for _ in range(5):
        time.sleep(5)
        btns = driver.find_elements(By.CSS_SELECTOR, "button, [role='button'], a")
        for b in btns:
            try:
                t = b.text or ""
                if "スキップ" in t or "Skip" in t: driver.execute_script("arguments[0].click();", b)
                if ("ウェブサイト" in t and "生成" in t) or "生成する" in t:
                    driver.execute_script("arguments[0].click();", b)
                    print("🟢 サイト構築フェーズへ移行します")
                    return True
            except: pass

    # 構築完了監視
    print("🚨 構築完了を監視します...")
    for i in range(30):
        time.sleep(40)
        is_ready = driver.execute_script("""
            const btns = Array.from(document.querySelectorAll('button, [role="button"], a'));
            const b = btns.find(el => (el.innerText || "").includes('公開'));
            if (!b) return false;
            return window.getComputedStyle(b).opacity > 0.8 && !b.disabled;
        """)
        if is_ready:
            print("✨ 「公開」ボタンがアクティブになりました！")
            time.sleep(10)
            return True
    return True


# ===============================
# サイト生成完了後のURL取得と公開確定フロー (v17)
# ===============================
def extract_published_url(driver):
    print("\n" + "="*40)
    print(" 🚀 超・確実URL抽出＆公開確定フロー v17")
    print("="*40)

    # ステップ0: バッジ等の強制排除
    driver.execute_script("""
        document.querySelectorAll('[class*="Overlay"], [class*="Portal"], [class*="badge"]').forEach(o => {
            if((o.innerText||'').includes('準備')) o.remove();
        });
    """)

    def scan_url_v17():
        return driver.execute_script("""
            let rawLines = [];
            document.querySelectorAll('*').forEach(el => {
                if (el.innerText) rawLines.push(el.innerText);
                if (el.value) rawLines.push(el.value);
                if (el.attributes) {
                    for (let a of el.attributes) {
                        if (a.value && (a.value.includes('readdy'))) rawLines.push(a.value);
                    }
                }
            });
            const matches = rawLines.join('\\n').match(/[a-zA-Z0-9.-]+\\.readdy\\.(link|co)[^\\s\\"'<> ]*/g);
            if (!matches) return null;
            let found = Array.from(new Set(matches))
                .map(u => u.replace(/^https?:\\/\\//, '').split(/[/?# ]/)[0])
                .filter(u => u.includes('readdy') && !u.includes('static.') && !u.includes('docs.'));
            if (found.length > 0) {
                found.sort((a,b) => a.length - b.length);
                return 'https://' + found[0];
            }
            return null;
        """)

    # ステップ1: ドメイン画面へ
    print("⏳ ステップ1: 「ドメイン」画面へ切り替えてURLを取得中...")
    for _ in range(3):
        driver.execute_script("""
            const items = Array.from(document.querySelectorAll('div, span, p, a, button'));
            const target = items.find(el => {
                const t = (el.innerText || el.textContent || "").trim();
                const r = el.getBoundingClientRect();
                return (t === 'ドメイン' || t === 'Domain') && r.left < 250 && r.width > 0;
            });
            if (target) target.click();
        """)
        time.sleep(5)
        url = scan_url_v17()
        if url: break
    
    if url:
        print(f"👉 捕捉したURL: {url}")
    else:
        print("❌ URLの捕捉に失敗しました。")

    # ステップ2: 公開確定 (特に中央の紫ボタンを確実に叩く)
    print("⏳ ステップ2: サイト公開ボタンを物理クリックします...")
    # 紫ボタン（ロケットアイコン付き）をターゲット
    driver.execute_script("""
        const btns = Array.from(document.querySelectorAll('button, [role="button"], div, a'));
        // 1. 文言に「公開/更新/Publish/Update」が含まれる
        // 2. 背景色が紫系統（rgb(112, 76, 255)など）か、SVGアイコンを含む
        const pBtn = btns.find(el => {
            const t = (el.textContent || "").trim();
            const r = el.getBoundingClientRect();
            const hasText = /公開|更新|Publish|Update/.test(t);
            const isPurple = window.getComputedStyle(el).backgroundColor.includes('rgb');
            const hasIcon = el.querySelector('svg');
            return hasText && r.width > 20 && r.top > 200;
        });
        if (pBtn) {
            pBtn.scrollIntoView({block: 'center'});
            ['mousedown', 'mouseup', 'click'].forEach(type => {
                pBtn.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
            });
        }
    """)
    time.sleep(5)
    
    # 物理マウスエミュレーション (念のため)
    try:
        wait = WebDriverWait(driver, 5)
        p_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., '公開') or contains(., 'Publish')]")))
        driver.execute_script("arguments[0].click();", p_btn)
    except: pass

    # ステップ3: モーダル内確定ボタンの待機と押下
    print("⏳ ステップ3: 確定モーダルのボタン（白）を待機中...")
    confirmed = False
    for i in range(10):
        res = driver.execute_script("""
            const btns = Array.from(document.querySelectorAll('button, [role="button"], div, a'));
            const b = btns.find(el => {
                const t = (el.textContent || "").trim();
                const r = el.getBoundingClientRect();
                // 画面中央に出現する白いボタン
                return /公開|確定|Confirm|Publish/.test(t) && r.top > 200 && r.top < (window.innerHeight - 200) && r.width > 30;
            });
            if (b) {
                b.click();
                ['mousedown', 'mouseup', 'click'].forEach(type => {
                    b.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
                });
                return true;
            }
            return false;
        """)
        if res:
            print("🔘 公開確定ボタンのクリックに成功しました！")
            confirmed = True; break
        time.sleep(2)
    
    driver.save_screenshot(os.path.abspath("debug_v17_final.png"))
    return url if url else "URL抽出失敗"


# ===============================
# ソースコードエクスポート (v17)
# ===============================
def export_source_code(driver):
    print("\n🚀 ソースコードエクスポート")
    # 0. エディター画面に戻る
    driver.execute_script("""
        const e = Array.from(document.querySelectorAll('div, span, button, a')).find(el => (el.innerText || "").trim() === 'エディター');
        if (e) e.click();
    """)
    time.sleep(5)

    driver.execute_script("document.querySelectorAll('[role=\"dialog\"], [class*=\"Overlay\"]').forEach(el => el.remove());")
    
    # 1. コードタブ
    driver.execute_script("""
        const t = Array.from(document.querySelectorAll('div, span, button, a')).find(el => ['コード', 'Code'].includes((el.innerText || "").trim()));
        if (t) t.click();
    """)
    time.sleep(5)
    
    # 2. ダウンロード
    for _ in range(5):
        found = driver.execute_script("""
            const b = Array.from(document.querySelectorAll('button, [role="button"], a, div'))
                .find(el => /エクスポート|Export|ダウンロード|Download/.test(el.innerText) && el.getBoundingClientRect().width > 10);
            if (b) { b.click(); return true; }
            return false;
        """)
        if found: break
        time.sleep(4)
    
    time.sleep(5)
    # 3. Zip確認
    driver.execute_script("""
        const next = Array.from(document.querySelectorAll('button, a')).find(el => /Zip|Confirm|ダウンロード|エクスポート/.test(el.innerText));
        if(next) next.click();
    """)
    
    download_dir = os.path.abspath("downloads")
    for _ in range(15):
        time.sleep(4)
        zips = [f for f in os.listdir(download_dir) if f.endswith('.zip')]
        if zips:
            p = os.path.join(download_dir, zips[-1])
            if os.path.exists(p) and os.path.getsize(p) > 0: return p
    return None


def run_flow():
    print("======================================")
    print(" Readdy.ai 自動化 v17 起動")
    print("======================================")
    
    sheet = get_sheet()
    jobs = get_new_jobs(sheet)
    if not jobs:
        print("新規案件なし"); return

    job = jobs[0]; row = job["_row"]
    update_status(sheet, row, "processing")
    driver = start_driver()

    try:
        driver.get("https://readdy.ai/project")
        time.sleep(8)

        fill_readdy_form(driver, job)
        process_readdy_generation(driver, job)
        
        final_url = extract_published_url(driver)
        if final_url and "抽出失敗" not in final_url:
            update_result_url(sheet, row, final_url)
            
        zip_path = export_source_code(driver)
        
        delivery_zip = None
        if zip_path:
            optimized_dir = process_downloaded_zip(zip_path, job)
            if optimized_dir:
                delivery_zip = shutil.make_archive(f"{optimized_dir}_optimized", 'zip', optimized_dir) + ".zip"
        
        if not final_url or "抽出失敗" in final_url:
            update_status(sheet, row, "error (url_failed)")
            return

        client_email = next((str(v).strip() for k, v in job.items() if any(kw in str(k).lower() for kw in ["メールアドレス", "email"])), "")
        if client_email:
            success = send_delivery_email(client_email, job.get("会社名", "お客様"), final_url, delivery_zip)
            update_status(sheet, row, "delivered" if success else "done (mail_failed)")
        else:
            update_status(sheet, row, "done")
        
        print("✅ 全工程完了")

    except Exception as e:
        print(f"❌ エラー発生: {e}"); update_status(sheet, row, "error")
    finally:
        print("終了")

def process_downloaded_zip(zip_path, job):
    base = os.path.dirname(zip_path)
    extract_dir = os.path.join(base, f"site_{job.get('_row', 'unknown')}")
    if not os.path.exists(extract_dir): os.makedirs(extract_dir)
    with zipfile.ZipFile(zip_path, 'r') as zf: zf.extractall(extract_dir)
    target = extract_dir
    for r, d, f in os.walk(extract_dir):
        if any(x.endswith('.html') for x in f): target = r; break
    return target if optimize_website(target, job) else None

if __name__ == "__main__":
    run_flow()