import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

LOG_FILE = "update_log_v12.txt"
def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

PROFILE_PATH = r"C:\readdy_profile"

def setup_driver():
    options = Options()
    options.add_argument(f"user-data-dir={PROFILE_PATH}")
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,3000")
    return webdriver.Chrome(options=options)

def js_force_update(driver, target_url, site_name, text):
    log(f"[*] {site_name} をV12(JS介入)で攻略中...")
    driver.get(target_url)
    time.sleep(15)
    
    # 1. リンクを走査してモード切替を強行
    js_click_mode = """
    var links = document.querySelectorAll('a');
    for(var i=0; i<links.length; i++){
        var t = links[i].innerText;
        if(t.includes('ワーカーメニュー') || t.includes('受注モード') || t.includes('受注メニュー')){
            links[i].click();
            return true;
        }
    }
    return false;
    """
    if driver.execute_script(js_click_mode):
        log(f"[!] {site_name}: JSによるモード切替リンクのクリックに成功。待機中...")
        time.sleep(15)
        driver.get(target_url)
        time.sleep(10)

    # 2. 入力欄をJSで特定して入力
    js_fill = f"""
    var tas = document.querySelectorAll('textarea');
    var target = null;
    for(var i=0; i<tas.length; i++){{
        var n = tas[i].name.toLowerCase();
        if(n.includes('intr') || n.includes('profile') || n.includes('summary') || n.includes('about')){{
            target = tas[i]; break;
        }}
    }}
    if(!target && tas.length > 0) target = tas[0];
    if(target){{
        target.value = `{text}`Index;
        var event = new Event('input', {{ bubbles: true }});
        target.dispatchEvent(event);
        return true;
    }}
    return false;
    """
    if driver.execute_script(js_fill):
        log(f"[SUCCESS] {site_name}: JSによる入力に成功。保存ボタンを探します。")
        
        # 3. 保存ボタンをJSでクリック
        js_save = """
        var btns = document.querySelectorAll('input[type="submit"], button, input[type="button"]');
        for(var i=0; i<btns.length; i++){
            var val = (btns[i].value || btns[i].innerText || "").trim();
            if(val.includes('保存') || val.includes('更新') || val.includes('確認')){
                btns[i].click();
                return val;
            }
        }
        return null;
        """
        btn_name = driver.execute_script(js_save)
        if btn_name:
            log(f"[!] {site_name}: '{btn_name}' をJSでクリック。")
            time.sleep(10)
            # クラウドワークスの確認画面対応
            if site_name == "CrowdWorks":
                driver.execute_script(js_save) # もう一度クリック（保存する）
                time.sleep(5)
            
            log(f"[FINISH] {site_name}: 反映完了。")
            driver.save_screenshot(f"v12_done_{site_name}.png")
            return True
    
    log(f"[ERROR] {site_name}: 攻略失敗。")
    driver.save_screenshot(f"v12_fail_{site_name}.png")
    return False

def main():
    text = """はじめまして。AIクリエイティブ・最速屋のヒロです。

最新のAI技術（GEO/LLMO/llms.txt等）を駆使し、これからのAI検索時代に勝ち残るWebサイトを「圧倒的な速さ」と「格安」で提供しております。

【提供可能サービス】
- GEO/LLMO（生成AI検索エンジンへの最適化）
- llms.txt 実裝（AIクローラー向け最新設計）
- SNS連動オートメーション（自動投稿・運用）
- Vibe Coding（AI駆動による超高速開発、最短24時間納品）

【実績例】
- 日本最大級のピックルボール総合情報ハブの構築
- オンライン教育支援プラットフォームの構築
- カフェ公式Webサイト制作 等

「最速でプロジェクトを立ち上げたい」「AIに最適化された最新のサイトが欲しい」という方は、ぜひお気軽にご相談ください。迅速に初回回答いたします。"""

    driver = setup_driver()
    try:
        js_force_update(driver, "https://crowdworks.jp/settings/profile/edit", "CrowdWorks", text)
        js_force_update(driver, "https://coconala.com/users/my/about", "Coconala", text)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
