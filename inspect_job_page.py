from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import textwrap

AUTO_SUBMIT = False

driver = webdriver.Chrome()
wait = WebDriverWait(driver, 20)

TARGET_URL = "https://crowdworks.jp/public/jobs/12992005"


def extract_text_safe(xpath_list):
    for xp in xpath_list:
        try:
            elem = driver.find_element(By.XPATH, xp)
            txt = elem.text.strip()
            if txt:
                return txt
        except Exception:
            pass
    return ""


def build_proposal(title: str, body: str) -> str:
    title_lower = title.lower()
    body_lower = body.lower()

    # 簡易判定
    is_web = any(word in (title + body) for word in [
        "web", "lp", "ホームページ", "ランディングページ", "サイト制作",
        "seo", "llmo", "geo", "ai検索", "集客", "wordpress"
    ])

    is_video = any(word in (title + body) for word in [
        "動画", "youtube", "ショート", "tiktok", "編集"
    ])

    if is_web:
        return textwrap.dedent("""\
        はじめまして。

        AIを活用したWeb制作を専門としており、
        SEO・GEO・LLMO（AI検索最適化）に特化したページ制作を行っております。

        従来の制作とは異なり、
        検索エンジンだけでなくChatGPTなどのAI検索にも最適化された構造で構築可能です。

        また、AIを活用することで
        スピード・品質ともに高いレベルでの制作を実現しており、
        短期間での納品にも対応可能です。

        ご要望に応じて柔軟に対応いたしますので、
        ぜひ一度お話しできれば幸いです。

        よろしくお願いいたします。
        """)

    if is_video:
        return textwrap.dedent("""\
        はじめまして。

        AIを活用したクリエイティブ制作とWeb導線設計を行っております。
        特に、集客導線を意識した構成設計や、AIを活用したスピーディーな制作対応が可能です。

        単なる作業ではなく、
        見てもらう・伝わる・成果につながる構成を意識して対応いたします。

        迅速なコミュニケーションと柔軟な修正対応を心がけておりますので、
        ぜひ一度ご相談いただければ幸いです。

        よろしくお願いいたします。
        """)

    return textwrap.dedent("""\
    はじめまして。

    AIを活用したWeb制作・コンテンツ制作を行っております。
    SEO・GEO・LLMOを意識した構成設計と、スピーディーな制作対応を強みとしております。

    ご要望を丁寧に確認しながら、
    目的に合った形で柔軟に対応いたします。

    ぜひ一度お話しできれば幸いです。
    よろしくお願いいたします。
    """)


# ログイン
driver.get("https://crowdworks.jp/login")
input("ログインしてください → ログイン後に Enter: ")

# 案件ページ
driver.get(TARGET_URL)

# タイトル取得
title = extract_text_safe([
    "//h1",
    "//h2",
])

# 本文取得
body = extract_text_safe([
    "//div[contains(@class,'job_offer_detail')]",
    "//section[contains(., '仕事内容')]",
    "//body",
])

print("案件タイトル:", title[:120])
print("本文先頭:", body[:200].replace("\n", " "))

# 応募ボタン
apply_btn = wait.until(
    EC.presence_of_element_located((By.XPATH, "//a[contains(., '応募')]"))
)
driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", apply_btn)
time.sleep(1)

try:
    apply_btn.click()
except Exception:
    driver.execute_script("arguments[0].click();", apply_btn)

time.sleep(3)

# 相談してから金額を提案 を選ぶ
try:
    consult_radio = driver.find_element(
        By.XPATH,
        "//*[contains(text(),'相談してから金額を提案')]"
    )
    driver.execute_script("arguments[0].click();", consult_radio)
    print("金額提案方法: 相談してから金額を提案")
except Exception:
    print("金額提案方法の切替はスキップ")

# 応募文生成
message = build_proposal(title, body)

# textarea取得
textarea = wait.until(
    EC.presence_of_element_located((By.TAG_NAME, "textarea"))
)

driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", textarea)
time.sleep(1)

textarea.clear()
textarea.send_keys(message)

print("応募文入力完了")
print("=" * 50)
print(message)
print("=" * 50)

if AUTO_SUBMIT:
    submit_btn = wait.until(
        EC.presence_of_element_located((By.XPATH, "//button[contains(., '応募する')]"))
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
    time.sleep(1)
    try:
        submit_btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", submit_btn)
    print("送信完了")
else:
    print("AUTO_SUBMIT=False のため送信していません。画面を確認してください。")

input("確認後 Enter で終了")
driver.quit()