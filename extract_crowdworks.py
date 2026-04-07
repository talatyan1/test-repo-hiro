import sys
import os
import time
import json
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Windows環境での出力エラー対策
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def extract_crowdworks():
    print("CrowdWorks案件抽出を自動実行中...")
    options = Options()
    # 既存の Chrome プロファイルを使用 (app.py に準拠)
    profile_path = r"C:\readdy_profile"
    options.add_argument(f"--user-data-dir={profile_path}")
    options.add_argument("--headless=new") # ヘッドレスで実行
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    # 既存のプロセスとの競合を避けるためのオプション
    options.add_argument("--remote-debugging-port=9222")
    
    try:
        driver = webdriver.Chrome(options=options)
        wait = WebDriverWait(driver, 20)
        
        url = "https://crowdworks.jp/public/jobs/category/1"
        driver.get(url)
        time.sleep(5)
        
        # 案件要素の待機
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".job_item")))
        
        job_elements = driver.find_elements(By.CSS_SELECTOR, ".job_item")
        jobs = []
        
        for item in job_elements[:20]:
            try:
                title_el = item.find_element(By.CSS_SELECTOR, ".item_title a")
                title = title_el.text.strip()
                link = title_el.get_attribute("href")
                
                reward = "不明"
                try:
                    reward = item.find_element(By.CSS_SELECTOR, ".amount").text.strip()
                except: pass
                
                desc = ""
                try:
                    desc = item.find_element(By.CSS_SELECTOR, ".job_summary").text.strip()
                except: pass
                
                jobs.append({
                    "title": title,
                    "url": link,
                    "reward": reward,
                    "description": desc
                })
            except Exception as e:
                continue
                
        print(f"Success: {len(jobs)} items extracted.")
        
        # 保存先ディレクトリの作成
        output_dir = "Hiro/crowd_agent/data/results"
        os.makedirs(output_dir, exist_ok=True)
        
        csv_file = os.path.join(output_dir, "crowdworks_jobs_automated.csv")
        json_file = os.path.join(output_dir, "crowdworks_jobs_automated.json")
        
        # CSV保存
        with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["title", "url", "reward", "description"])
            writer.writeheader()
            writer.writerows(jobs)
            
        print(f"CSV saved to: {csv_file}")
        
        # JSON保存
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
            
        print(f"JSON saved to: {json_file}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        try:
            driver.quit()
        except: pass

if __name__ == "__main__":
    extract_crowdworks()
