import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

LOG_FILE = "portfolio_log_v2.txt"
def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

PROFILE_PATH = r"C:\readdy_profile"
ARTIFACT_DIR = r"C:\Users\nagas\.gemini\antigravity\brain\4594127f-316c-424e-8ae5-fea77e6f680c"

PORTFOLIOS = [
    {
        "title": "日本最大級のピックルボール総合情報ハブ",
        "description": "最新のAI（LLMO）に対応したコミュニティポータル。自動情報収集とSEO最適化を実装。",
        "image": os.path.join(ARTIFACT_DIR, "pickleball_ss_1774531041489.png"),
        "url": "https://pickleballjapanhub.jp/"
    },
    {
        "title": "オンライン教育支援プラットフォーム (Prep Online)",
        "description": "教育機関向けの学習管理システム。GEO最適化により地域検索に強いサイト構成を実現。",
        "image": os.path.join(ARTIFACT_DIR, "prep_ss_1774531009542.png"),
        "url": "https://prep.online.jp/"
    }
]

def setup_driver():
    options = Options()
    options.add_argument(f"user-data-dir={PROFILE_PATH}")
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,3000")
    return webdriver.Chrome(options=options)

def upload_lancers_v2(driver, item):
    log(f"[*] Lancers V2: ポートフォリオ登録開始 - {item['title']}")
    driver.get("https://www.lancers.jp/mypage/portfolio/add")
    time.sleep(15)
    
    try:
        # Title (Lancers uses specific name attributes)
        # 実際にページを読み込んでtextareaやinput[name*='title']を探す
        inputs = driver.find_elements(By.TAG_NAME, "input")
        found = False
        for inp in inputs:
            name = inp.get_attribute("name") or ""
            if "Portfolio" in name and "title" in name.lower():
                inp.send_keys(item['title'])
                found = True; break
        
        if not found:
            log("[ERROR] Lancers: タイトル入力欄が見つかりません。")
            driver.save_screenshot("lancers_portfolio_err.png")
            return False

        # Description
        tas = driver.find_elements(By.TAG_NAME, "textarea")
        for ta in tas:
            name = ta.get_attribute("name") or ""
            if "Portfolio" in name and "description" in name.lower():
                ta.send_keys(item['description'])
                break

        # File
        files = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        if files:
            files[0].send_keys(item['image'])
            time.sleep(5)

        # Submit
        submits = driver.find_elements(By.CSS_SELECTOR, "input[type='submit'], button[type='submit']")
        for s in submits:
            val = (s.get_attribute("value") or s.text or "").strip()
            if "保存" in val or "登録" in val or "確認" in val:
                driver.execute_script("arguments[0].click();", s)
                time.sleep(10)
                log(f"[SUCCESS] Lancers: {item['title']} 完了")
                return True
        
        return False
    except Exception as e:
        log(f"[ERROR] Lancers: {e}")
        return False

def main():
    driver = setup_driver()
    try:
        # CWは完了済みなのでLancersのみリトライ
        for item in PORTFOLIOS:
            upload_lancers_v2(driver, item)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
