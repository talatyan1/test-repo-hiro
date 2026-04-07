import smtplib
from email.message import EmailMessage
import os

def send_delivery_email(to_email, client_name, preview_url, zip_path=None):
    """
    完成したサイトURLとソースコード(Zip)をクライアントへ自動返信する関数
    """
    if not to_email:
        print("⚠ クライアントのメールアドレスが指定されていないため、自動納品メールをスキップします。")
        return False
        
    print(f"\n======================================")
    print(" 📧 自動納品メール送信フェーズ")
    print("======================================")
    
    # 環境変数から送信用Gmailアカウントとアプリパスワードを取得
    # ※ 事前に .env 等で設定しておく必要があります
    sender_email = os.environ.get("GMAIL_ADDRESS")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    
    if not sender_email or not app_password:
        print("⚠ GMAIL_ADDRESS または GMAIL_APP_PASSWORD が設定されていません。")
        print("   自動納品メール機能を利用するには、.envファイルにGmail設定を追加してください。")
        return False
        
    msg = EmailMessage()
    msg['Subject'] = f"【納品完了】{client_name}様 Webサイトの自動制作が完了いたしました"
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Bcc'] = sender_email # 送信確認のためにBCCを追加
    
    content = f"""{client_name} 様

この度はAIによるWebサイト自動制作・SEO最適化システムをご利用いただき、誠にありがとうございます。
ご入力いただいた要件をもとに、次世代AI検索（GEO/LLMO）対応のWebサイト構築が完了いたしましたので、ご報告申し上げます。

以下より、プレビューURLをご確認いただけます。

▼完成サイトのプレビューURL
{preview_url or "（URLの取得に失敗しました。管理画面から直接ご確認ください）"}


【納品ファイルについて】
納品用のソースコード（SEOタグ・LLMs.txt最適化済みZipファイル）は、本メールに添付しております。
解凍の上、ご指定のサーバー等へのアップロード（デプロイ）にご活用ください。

ご不明点等がございましたら、お気軽にお問い合わせください。
今後ともよろしくお願い申し上げます。
"""
    msg.set_content(content)
    
    # 納品用Zipファイルをメールに添付する
    if zip_path and os.path.exists(zip_path):
        import mimetypes
        ctype, encoding = mimetypes.guess_type(zip_path)
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
            
        ctype_str = str(ctype)
        maintype, subtype = ctype_str.split('/', 1)
        
        try:
            with open(zip_path, 'rb') as fp:
                msg.add_attachment(fp.read(),
                                   maintype=maintype,
                                   subtype=subtype,
                                   filename=os.path.basename(zip_path))
            print(f"📎 添付ファイルを追加しました: {os.path.basename(zip_path)}")
        except Exception as e:
            print(f"⚠ 添付ファイルの読み込みエラー: {e}")
    else:
        print("⚠ 添付用のZipファイルが見つかりません。リンクのみ送信します。")

    # SMTPサーバー (Gmail) 経由で送信
    try:
        print("⏳ はじめてのSMTP接続を確立しています...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(str(sender_email), str(app_password))
            smtp.send_message(msg)
        print(f"✅ {to_email} 宛に自動納品メールを送信完了しました！")
        return True
    except smtplib.SMTPAuthenticationError:
        print("❌ メール送信エラー（認証失敗）: アプリパスワードが間違っているか、2段階認証の設定をご確認ください。")
        return False
    except Exception as e:
        print(f"❌ メール送信エラー: {e}")
        return False
