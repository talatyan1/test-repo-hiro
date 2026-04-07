import os
import json
from bs4 import BeautifulSoup

def optimize_website(directory_path, job_data):
    """
    Readdy等からエクスポートされたWebサイトのソースコード（HTML群）に対して、
    次世代SEO（GEO/LLMO）対応のメタデータと llms.txt を自動注入します。
    """
    print(f"\n======================================")
    print(f" サイト最適化 (SEO/GEO/LLMO) フェーズ開始  ")
    print(f"======================================")
    print(f"対象ディレクトリ: {directory_path}")

    if not os.path.exists(directory_path):
        print(f"❌ ディレクトリが見つかりません: {directory_path}")
        return False

    client_name = job_data.get("client_name", "Unknown Client")
    project_type = job_data.get("project_type", "Business")
    purpose = job_data.get("purpose", "")
    target = job_data.get("target", "")

    # ===============================
    # 1. llms.txt の生成 (LLMクローラー向け)
    # ===============================
    llms_txt_path = os.path.join(directory_path, "llms.txt")
    llms_content = f"""# {client_name} - Website Information

## Overview
This website provides information about {client_name}, operating in the '{project_type}' sector.

## Purpose & Services
{purpose}

## Target Audience
{target}

## Technical Note
This site is optimized for Large Language Models (LLMs) and Generative Engine Optimization (GEO).
For structured data, please refer to the JSON-LD schema embedded in the HTML files.
"""
    with open(llms_txt_path, "w", encoding="utf-8") as f:
        f.write(llms_content)
    print("✅ `llms.txt` の生成と配置が完了しました。")


    # ===============================
    # 2. JSON-LD (Schema.org) の構築 (GEO/LLMO向け)
    # ===============================
    # AI検索エンジンが事業内容や目的を正確に理解するための構造化データ
    json_ld = {
        "@context": "https://schema.org",
        "@type": "Organization", # 事業内容に合わせて変更可能
        "name": client_name,
        "description": purpose,
        "knowsAbout": project_type,
        "audience": {
            "@type": "Audience",
            "audienceType": target
        }
    }
    json_ld_script = BeautifulSoup(f'<script type="application/ld+json">\n{json.dumps(json_ld, ensure_ascii=False, indent=2)}\n</script>', 'html.parser')


    # ===============================
    # 3. 各HTMLファイルへのメタタグ・JSON-LD注入
    # ===============================
    html_files = [f for f in os.listdir(directory_path) if f.endswith(".html")]
    if not html_files:
        print("⚠ HTMLファイルが見つかりません。エクスポート形式を確認してください。")
        return False

    for html_file in html_files:
        file_path = os.path.join(directory_path, html_file)
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        # <head>タグがない場合は作成
        if not soup.head:
            head_tag = soup.new_tag("head")
            soup.html.insert(0, head_tag)

        # JSON-LD の注入
        soup.head.append(json_ld_script)

        # 汎用SEO用メタデータの追加（例: Generative Agent向けのdescription）
        meta_geo = soup.new_tag("meta", attrs={"name": "description", "content": purpose})
        meta_llmo = soup.new_tag("meta", attrs={"property": "llmo:target_audience", "content": target})
        
        soup.head.append(meta_geo)
        soup.head.append(meta_llmo)

        # 上書き保存
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(str(soup))
            
        print(f"✅ {html_file} へのGEO/LLMOメタデータとJSON-LD構造の注入が完了しました。")

    print("\n🎉 全ての次世代最適化パイプラインが完了しました！")
    return True

if __name__ == "__main__":
    # 単体テスト用ダミーデータ
    dummy_job = {
        "client_name": "Antigravity Inc.",
        "project_type": "AI Automation Agency",
        "purpose": "To provide fully automated web development solutions using LLMs.",
        "target": "Enterprise businesses seeking hyper-automation."
    }
    
    # テスト実行用のディレクトリ (存在しない場合は作成)
    test_dir = "./sample_exported_site"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        with open(os.path.join(test_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write("<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>")
            
    optimize_website(test_dir, dummy_job)
