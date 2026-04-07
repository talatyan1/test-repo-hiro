---
name: crowd_agent
description: クラウドソーシングサイト（CrowdWorks, Lancers, Coconala）の巡回、AIによる案件判定、提案文生成、およびPlaywrightを用いた自動応募を行うスキル。
---

# クラウドソーシング自動化スキル (Crowd Agent Skill)

このスキルは、フリーランスや制作会社がクラウドソーシングサイトでの営業活動を自動化するためのものです。

## 主要機能

1.  **マルチサイト巡回**:
    - **CrowdWorks**, **Lancers**, **Coconala** から新着案件を自動取得。
    - 重複案件の排除（SQLAlchemy/SQLiteによる案件管理）。
2.  **AI判定 & プロンプト最適化**:
    - OpenAI API (GPT-4o等) を使用し、案件が自分のスキルにマッチするかを判定。
    - クライアントの課題を解決する、質の高い提案文を自動生成。
3.  **Playwright 自動応募**:
    - ブラウザ自動操作によるフォーム入力と応募完了までの実行。
    - UI変更を検知しAIで自動修復する「UI Resolver」機能を搭載。
4.  **通知統合**:
    - 応募結果を Slack およびメールでリアルタイム通知。
5.  **定期実行**:
    - Windowsタスクスケジューラによる定時巡回（10時, 15時, 17時）。

## セットアップ手順

### 1. 環境変数の設定
`.env` ファイルに以下の情報を設定してください。
- `OPENAI_API_KEY`: AI判定と提案生成に使用。
- `SLACK_WEBHOOK_URL`: 結果通知用。
- `GOOGLE_FORM_URL`: 提案文に含めるためのポートフォリオ/問い合わせフォームURL。

### 2. セッションの更新 (重要)
自動応募にはブラウザのログインセッションが必要です。
```powershell
python refresh_sessions.py
```
このコマンドを実行するとブラウザが起動します。手動でログイン後、コンソールで Enter を押すとセッションが保存されます。

## 使用方法

### 定期実行の登録
```powershell
powershell -ExecutionPolicy Bypass -File setup_tasks.ps1
```

### 即時実行
```powershell
.venv\Scripts\python.exe main.py
```

## メンテナンスとトラブルシューティング

- **セッション切れ**: 応募が「ログイン状態ファイルが見つかりません」または「セッション切れ」で失敗し始めたら、`refresh_sessions.py` を再実行してください。
- **UI変更**: サイトのデザイン変更でボタンが見つからない場合、自動的に `UIResolver` が起動し、AIが新しいボタンを特定しようと試みます。
- **ログの確認**: `logs/` ディレクトリ内のログファイルと、`logs/screenshots/` 内のスクリーンショットでエラー原因を特定できます。
