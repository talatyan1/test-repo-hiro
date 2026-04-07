# クラウドソーシング自動化 MVP: 実行手順・運用ガイド

## A. 実行手順（コピペ用）

Windowsのコマンドプロンプト（cmd.exe）を開き、以下のコマンドを1行ずつコピー＆ペーストして実行してください。

```cmd
cd C:\Users\nagas\.gemini\antigravity\Hiro\crowd_agent
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py
```

※ **ポイント**: `Activate.ps1` はPowerShell用であり、標準のセキュリティ制限で弾かれます。コマンドプロンプト（cmd）から `.bat` を呼び出すのが最も確実で安全な方法です。

## B. PowerShellを使う場合の安全な設定方法

どうしてもPowerShell上で仮想環境をアクティベートしたい場合は、管理者権限でPowerShellを開き、以下のコマンドでカレント・ユーザーのみ実行ポリシーを「RemoteSigned（ローカルスクリプトは許可）」に変更します。

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```
※完了後 `Y` を入力して確定してください。システム全体ではなく現在のユーザーのみに適用されるため、セキュリティリスクを最小限に抑えられます。

## C. 初回テスト手順

1. **環境変数の設定**
   - `.env` ファイルを開き、`OPENAI_API_KEY` と `SLACK_WEBHOOK_URL` にご自身の正しいキーを入力します。
2. **テストデータの準備**
   - `data/input/` フォルダの中に、既存のexeが出力した **1件だけ案件が入っている** テスト用Excelファイル（例: `test.xlsx`）を配置します。
3. **実行と確認**
   - コマンドプロンプトから `python main.py` を実行（または `run_flow.bat` をダブルクリック）します。
4. **確認ポイント（成功判定条件）**
   - **重複チェック**: `logs/app.log` に「DBに 1 件の新規案件を登録しました」と出ること。
   - **AI判定**: `logs/ai.log` に「案件(...)判定: True」等と出ること。
   - **Slack通知**: ご自身のSlackにテスト案件の内容とAIの判定結果、応募文フォーマットが飛んでくること。
   - **ファイル移動**: `data/input/test.xlsx` が `data/archive/test.xlsx` に移動していること。
5. **再実行テスト（重複防止の確認）**
   - もう一度同じ `test.xlsx` を `input` フォルダに戻して実行し、Slackに通知が **来ない**（DBで弾かれている）ことを確認します。

## D. よくあるエラーと対処一覧

| エラーの発生箇所 | 代表的なエラーメッセージ | 主な原因と対処法 |
| :--- | :--- | :--- |
| **pandas/Excel読込** | `Missing optional dependency 'openpyxl'` | 仮想環境のアクティベート漏れ、または `pip install openpyxl` が失敗している。再度上記「A」の手順を実行。 |
| **Excel列名不一致** | `KeyError: 'タイトル'` | exeが出力するExcelの列名（1行目）が、`src/excel_reader.py` が想定している名前（タイトル、URL等）と違う。`excel_reader.py` の辞書マッピング部分を実際のExcelの列名に合わて修正する。 |
| **OpenAI API** | `openai.AuthenticationError` / `RateLimitError` | APIキーが間違っている、または課金登録・残高不足。`.env` を確認。一時的なエラーの場合は `ai_judge.py` 内の tenacity により自動でリトライされます。 |
| **Slack通知** | `requests.exceptions.HTTPError: 400 Client Error` | `.env` のWebhook URLが間違っているか、送信するJSONフォーマット（Block Kit）の記述エラー。`logs/error.log` を確認する。 |
| **DBエラー** | `sqlite3.OperationalError: database is locked` | SQLiteを開いたまま強制終了した場合に発生。PCを再起動するか、タスクマネージャーから残っている `python.exe` を消す。 |

## E. 今後の拡張優先順位

MVP（データ読取〜AI判定〜Slack通知）が安定稼働した後のステップです。

1. **既存exeとPythonの統合管理（バッチの完成）**
   - 既存の `scrape_data.exe` を `run_flow.bat` の中（Phase 1部分）に組み込み、exeの完了を待ってからPythonが動く連結フローを完成させます。
2. **タスクスケジューラ登録（完全自動実行）**
   - Windowsのタスクスケジューラに `run_flow.bat` を登録し、「毎日8:00と15:00」等に自動で裏で動くように設定します。
3. **Playwrightによるクローラーの再実装（脱ブラックボックス）**
   - 既存exeがクラウドソーシング側のサイト仕様変更で動かなくなったタイミングで、Pythonの `Playwright` を使ってクローラー部分を新しく書き直します。
4. **自動応募（最終目標）**
   - スパム対策（CAPTCHA等）のリスクを評価した上で、Slackからのボタンアクション（承認フロー）を起点に、Playwrightを使って対象サイトへ自動でフォーム入力と送信（応募）を行うモジュールを追加します。
