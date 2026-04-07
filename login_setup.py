import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def main():
    profile_path = os.path.abspath("chrome_profile")
    print(f"セッション維持用のプロファイル保存先: {profile_path}")
    
    options = Options()
    options.add_argument(f"--user-data-dir={profile_path}")
    
    print("ブラウザを起動しています（画面が表示されます）...")
    driver = webdriver.Chrome(options=options)
    driver.get("https://crowdworks.jp/login")
    
    print("\n" + "="*50)
    print("【初回のログイン処理のお願い】")
    print("起動したChromeブラウザ上でクラウドワークスにログインを行ってください。")
    print("ロボット判定等が出た場合は手動でクリアしてください。")
    print("ログインが完全に完了し、マイページが表示されたら、")
    print("このターミナルで「Enter」キーを押してください。")
    print("="*50 + "\n")
    
    input("ログイン完了後、ここをクリックしてEnterを押してください > ")
    driver.quit()
    print("プロファイルが保存されました！これで app.py 側からも自動でログイン状態が継承されます。")

if __name__ == "__main__":
    main()
