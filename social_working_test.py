import time
import os
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

PROFILE_PATH = r"C:\readdy_profile"
# キーワード「ホームページ作成」で検索
QUERY = "ホームページ作成"
SEARCH_URL = f"https://crowdworks.jp/public/jobs/search?q={urllib.parse.quote(QUERY)}"

def setup_driver():
    options = Options()
    options.add_argument(f"user-data-dir={PROFILE_PATH}")
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)

def extract_latest_jobs(driver):
    print(f"[*] 検索URLにアクセス中: {SEARCH_URL}")
    driver.get(SEARCH_URL)
    time.sleep(5)
    
    jobs = []
    # 案件タイトルのリンクを取得 (h3 > a または類似)
    links = driver.find_elements(By.CSS_SELECTOR, "h3.item_title a")
    for link in links[:10]:
        try:
            title = link.text.strip()
            url = link.get_attribute("href")
            if "jobs" in url:
                jobs.append({"title": title, "url": url})
        except: continue
    return jobs

def get_job_detail(driver, job_url):
    print(f"[*] 詳細取得中: {job_url}")
    driver.get(job_url)
    time.sleep(3)
    try:
        # 詳細エリア (複数の可能性があるが、一般的なものを探す)
        desc_box = driver.find_elements(By.CSS_SELECTOR, ".job_description_box, .job-description")
        if desc_box:
            return desc_box[0].text.strip()
        return "詳細エリア見つからず"
    except:
        return "詳細取得エラー"

def main():
    driver = setup_driver()
    try:
        jobs = extract_latest_jobs(driver)
        if not jobs:
            print("案件が見つかりませんでした。セレクタを確認してください。")
            driver.save_screenshot("search_fail.png")
            return
        
        results = []
        # 相対パスを絶対パスへ変換
        for job in jobs[:3]: # 上位3件を解析
            detail = get_job_detail(driver, job['url'])
            results.append({
                "title": job['title'],
                "url": job['url'],
                "description": detail
            })
            
        with open("candidate_jobs.txt", "w", encoding="utf-8") as f:
            for i, res in enumerate(results, 1):
                f.write(f"ID: {i}\n")
                f.write(f"TITLE: {res['title']}\n")
                f.write(f"URL: {res['url']}\n")
                f.write(f"DESCRIPTION:\n{res['description']}\n")
                f.write("-" * 50 + "\n")
        print(f"[*] {len(results)} 件の案件を candidate_jobs.txt に保存完了")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
