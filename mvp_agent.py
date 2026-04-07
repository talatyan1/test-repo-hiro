import time
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

def setup_driver():
    options = Options()
    # options.add_argument('--headless') # コメントアウトで画面を表示し動作を可視化
    
    # 既存の geckodriver.exe がある場合はそちらを通す
    # 無い場合、Selenium 4以降は自動でドライバーを管理・ダウンロードします
    try:
        service = Service(executable_path="exe/geckodriver.exe")
        driver = webdriver.Firefox(service=service, options=options)
    except Exception:
        # パスが見つからない場合は自動管理を利用
        driver = webdriver.Firefox(options=options)
    
    driver.implicitly_wait(10)
    return driver

def extract_jobs(driver, url: str) -> List[Dict[str, str]]:
    """
    【フェーズ2】 案件URLの正確な抽出
    """
    print(f"[*] 案件一覧ページにアクセス中: {url}")
    driver.get(url)
    time.sleep(3) # JavaScriptの読み込み待機 (クラウドワークスの動的描画用)
    
    jobs = []
    # クラウドワークスの案件リストアイテムのセレクタ
    job_elements = driver.find_elements(By.CSS_SELECTOR, ".job_item")
    
    for item in job_elements:
        try:
            # タイトルとURLを取得
            title_el = item.find_element(By.CSS_SELECTOR, ".item_title a")
            title = title_el.text.strip()
            job_url = title_el.get_attribute("href")
            
            # 相対パスの場合は絶対パスに補完
            if job_url and job_url.startswith('/'):
                job_url = f"https://crowdworks.jp{job_url}"
                
            jobs.append({
                "title": title,
                "url": job_url
            })
        except Exception:
            # 万が一1件の要素取得に失敗してもループを止めずに次の案件へ
            continue
            
    print(f"[抽出完了] 計 {len(jobs)} 件の案件URLを取得しました。")
    return jobs

def filter_web_jobs(jobs: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    【フェーズ3】 Web制作案件のみ抽出
    """
    print("\n[*] 「Web制作」関連の案件をフィルタリング中...")
    
    # Web制作案件とみなすキーワード群
    keywords = ["web", "ホームページ", "lp", "コーディング", "デザイン", "サイト"]
    filtered_jobs = []
    
    for job in jobs:
        target_text = job["title"].lower()
        if any(keyword in target_text for keyword in keywords):
            filtered_jobs.append(job)
            
    print(f"[フィルタ完了] Web制作関連の案件として {len(filtered_jobs)} 件を抽出しました。")
    return filtered_jobs

def main():
    print("=== クラウドソーシング自動エージェント MVP ===")
    
    # 対象: クラウドワークスのカテゴリ別案件一覧ページ (例として「ホームページ作成・Webデザイン」カテゴリ)
    CROWDWORKS_URL = "https://crowdworks.jp/public/jobs/category/1"
    
    driver = None
    try:
        # ドライバ起動
        driver = setup_driver()
        
        # フェーズ2: アクセスと案件URL抽出
        all_jobs = extract_jobs(driver, CROWDWORKS_URL)
        
        # フェーズ3: 条件フィルタリング
        target_jobs = filter_web_jobs(all_jobs)
        
        # 抽出結果の出力
        print("\n=== 【最終抽出結果】 ===")
        if not target_jobs:
            print("該当する案件は見つかりませんでした。")
        else:
            for i, job in enumerate(target_jobs, 1):
                print(f"{i}. {job['title']}")
                print(f"   URL: {job['url']}\n")
                
    except Exception as e:
        print(f"\n[エラー] 実行中にエラーが発生しました: {e}")
    finally:
        if driver:
            print("[*] ブラウザを終了します...")
            driver.quit()

if __name__ == "__main__":
    main()
