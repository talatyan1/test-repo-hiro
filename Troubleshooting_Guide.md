# トラブルシューティングガイド

## 1. 応募ボタンが見つからない
- **原因**: サイト側の UI (HTML要素名など) が変更された、またはセッションが切れている。
- **対処**: 
  - `src/agent_actions.py` 内のセレクタを最新のものに更新する。
  - `refresh_sessions.py` を実行し、ブラウザを介して再ログインを行う。

## 2. API利用料の急増
- **原因**: AI判定の呼び出し回数が多すぎる。
- **対処**: 
  - `src/orchestrator.py` で新着案件の抽出条件（キーワード等）を絞り込む。
  - 抽出済みの重複案件を `src/deduplicator.py` が正しく弾いているか確認する。

## 3. Playwright / Selenium のエラー
- **原因**: ブラウザのバージョンが古い、またはヘッドレスモードでの描画問題。
- **対処**:
  - `playwright install chromium` でブラウザを最新にする。
  - 必要に応じて、`src/agent_actions.py` で `headless=False` に変更し、デバッグを行う。

## 4. Google Sheets 連携の失敗
- **原因**: `credentials.json` が読み込めない、またはスプレッドシートの権限設定。
- **対処**:
  - `src/` 配下に正しい `credentials.json` があるか確認。
  - スプレッドシートの共有設定に、サービスアカウントのアドレスを追加。
