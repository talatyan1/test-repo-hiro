import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 設定
PROFILE_PATH = r"C:\readdy_profile"
LOG_FILE = "capture_profile_log.txt"

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

def setup_driver():
    options = Options()
    options.add_argument(f"user-data-dir={PROFILE_PATH}")
    options.add_argument("--headless")
    options.add_argument("--window-size=1200,2000")
    return webdriver.Chrome(options=options)

def capture(driver, url, name):
    log(f"[*] {name} を取得中: {url}")
    driver.get(url)
    time.sleep(10) # 読み込み待機
    path = f"actual_profile_{name}.png"
    driver.save_screenshot(path)
    log(f"[SUCCESS] {name} キャプチャ完了: {path}")
    return path

def main():
    driver = setup_driver()
    try:
        # ランサーズ (公開プロフィール) - URLはmypageから類推するか直行
        # ヒロさんのLancers ID: talatyan1 (前回のSSより)
        capture(driver, "https://www.lancers.jp/profile/talatyan1", "Lancers")
        
        # クラウドワークス (ワーカープロフィール)
        # IDが不明な場合はマイページ経由
        driver.get("https://crowdworks.jp/dashboard")
        time.sleep(5)
        # 「ワーカーメニューに切り替える」があればクリック
        try:
            link = driver.find_elements(By.XPATH, "//a[contains(text(), 'ワーカーメニューに切り替える')]")
            if link:
                link[0].click()
                time.sleep(5)
        except: pass
        
        # 自分のプロフィールへ
        driver.get("https://crowdworks.jp/settings/profile/edit") # ここからプレビューボタンを探す手もあるが、URLを直接当てる
        # IDを抜くのが難しいので、一旦ダッシュボードのSSで代用、または固定リンク
        capture(driver, "https://crowdworks.jp/dashboard", "CrowdWorks_Dashboard")
        
        # ココナラ
        capture(driver, "https://coconala.com/users/my", "Coconala_MyPage")

    finally:
        driver.quit()

if __name__ == "__main__":
    from selenium.webdriver.common.by import By
    main()
