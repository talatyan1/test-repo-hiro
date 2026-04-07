import os
import json
import traceback

try:
    import gspread
    from google.oauth2.service_account import Credentials
    from gspread.exceptions import WorksheetNotFound
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False


# ==========================================
# 共通: Google Sheets クライアント取得
# ==========================================
def get_sheets_client(credentials_file="credentials.json"):
    if not GSPREAD_AVAILABLE:
        raise ImportError("gspread または google-auth がインストールされていません。")
    if not os.path.exists(credentials_file):
        raise FileNotFoundError(f"認証ファイルが見つかりません: {credentials_file}")
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
    return gspread.authorize(creds)


# ==========================================
# フェーズ1: CrowdWorks等の自動応募データ出力用
# ==========================================
def append_jobs_to_sheet(
    spreadsheet_id,
    jobs,
    worksheet_name="jobs",
    credentials_file="credentials.json",
):
    """
    jobs の配列を Google Sheets に追記する
    """
    client = get_sheets_client(credentials_file)
    sheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

    data_to_append = []
    for job in jobs:
        data_to_append.append([
            job.get("platform", ""),
            job.get("title", ""),
            job.get("url", ""),
            job.get("score", ""),
            job.get("priority", ""),
            job.get("reason", ""),
            job.get("proposal", ""),
            job.get("status", ""),
            job.get("checked_at", ""),
            job.get("applied_at", ""),
        ])

    if data_to_append:
        sheet.append_rows(data_to_append, value_input_option="USER_ENTERED")

    return len(data_to_append)

def export_to_google_sheets(
    rows,
    spreadsheet_id="11eOBB4_BF6QqfT_-9uluY_zhIvriBjVBvYyqyjP03m8",
    worksheet_name="jobs",
    credentials_file="credentials.json",
):
    print("\n[Google Sheets 連携 - 自動データ送信]")
    try:
        count = append_jobs_to_sheet(spreadsheet_id, rows, worksheet_name, credentials_file)
        print(f"  🚀 {count} 件の案件データを Google Sheets '{worksheet_name}' に送信完了しました！")
        return True
    except Exception as e:
        print(f"  ❌ Google Sheetsへの送信中にエラーが発生しました: {e}")
        return False


# ==========================================
# フェーズ2: Readdy 構成用 Google Form パイプライン
# ==========================================
def init_readdy_sheet(spreadsheet_id, worksheet_name, credentials_file):
    """
    Readdy用のシートが存在しない場合は自動作成し、ヘッダーをセットする。
    """
    client = get_sheets_client(credentials_file)
    ss = client.open_by_key(spreadsheet_id)
    
    try:
        sheet = ss.worksheet(worksheet_name)
    except WorksheetNotFound:
        # シートが存在しない場合は作成
        print(f"  [Info] シート '{worksheet_name}' が見つからないため新規作成します。")
        sheet = ss.add_worksheet(title=worksheet_name, rows=1000, cols=20)
        
    headers = [
        "timestamp", "client_name", "project_type", "purpose", "target", 
        "pages", "design_preference", "reference_url", "deadline", "status"
    ]
    
    # ヘッダーが不足または無い場合は書き込む
    current_headers = sheet.row_values(1)
    if not current_headers or current_headers[0] != "timestamp":
        sheet.insert_row(headers, 1)
        
    return sheet

# 列名マッピング辞書（フォーム項目名が多少変わっても対応）
COLUMN_MAPPING = {
    "timestamp": ["timestamp", "タイムスタンプ", "日時"],
    "client_name": ["client_name", "クライアント名", "会社名", "顧客名"],
    "project_type": ["project_type", "プロジェクトタイプ", "案件タイプ"],
    "purpose": ["purpose", "目的", "サイトの目的"],
    "target": ["target", "ターゲット", "対象者"],
    "pages": ["pages", "ページ数", "想定ページ"],
    "design_preference": ["design_preference", "デザイン希望", "デザインの希望"],
    "reference_url": ["reference_url", "参考URL", "参考サイト"],
    "deadline": ["deadline", "納期", "希望納期"],
    "status": ["status", "ステータス"]
}

def get_column_mapping(sheet):
    """
    シートのヘッダー行から列名マッピングを作成。
    戻り値: {標準キー: 実際の列インデックス}
    """
    headers = sheet.row_values(1)
    mapping = {}
    for std_key, possible_names in COLUMN_MAPPING.items():
        for idx, header in enumerate(headers):
            header_lower = header.lower().strip()
            if any(name.lower() in header_lower or header_lower in name.lower() for name in possible_names):
                mapping[std_key] = idx
                break
    return mapping

def fetch_new_readdy_jobs(spreadsheet_id="11eOBB4_BF6QqfT_-9uluY_zhIvriBjVBvYyqyjP03m8", worksheet_name="readdy_forms", credentials_file="credentials.json"):
    """
    status列が new または 空欄 の案件を取得し、抽出と同時に processing に更新する。
    戻り値: 新規案件のリストの各要素は辞書型
    """
    print(f"\n[Readdy Pipeline] スプレッドシート '{worksheet_name}' から新規案件を取得中...")
    try:
        sheet = init_readdy_sheet(spreadsheet_id, worksheet_name, credentials_file)
        mapping = get_column_mapping(sheet)
        
        if not mapping.get("status"):
            print("  ❌ status列が見つかりません。")
            return []
        
        # 全データを取得
        all_values = sheet.get_all_values()
        headers = all_values[0] if all_values else []
        data_rows = all_values[1:] if len(all_values) > 1 else []
        
        new_jobs = []
        updates = []
        
        for row_idx, row in enumerate(data_rows, start=2):  # 2行目から
            status_idx = mapping["status"]
            if status_idx >= len(row):
                continue
            status = str(row[status_idx]).strip().lower()
            if status in ["new", ""]:
                job_data = {"row_idx": row_idx}
                for std_key, col_idx in mapping.items():
                    if col_idx < len(row):
                        job_data[std_key] = row[col_idx]
                    else:
                        job_data[std_key] = ""
                new_jobs.append(job_data)
                
                # status列をprocessingに更新
                status_col = chr(ord('A') + status_idx)  # A=0, B=1, ...
                updates.append({
                    "range": f"{status_col}{row_idx}",
                    "values": [["processing"]]
                })
        
        # 一括でステータスを processing に更新
        if updates:
            sheet.batch_update(updates)
            print(f"  -> {len(new_jobs)}件の新規案件を検出し、ステータスを 'processing' に更新しました。")
        else:
            print("  -> 新規案件はありませんでした。")
            
        return new_jobs

    except Exception as e:
        print(f"  ❌ Readdy 案件の取得中に例外エラーが発生: {e}")
        traceback.print_exc()
        return []

def update_readdy_job_status(spreadsheet_id, row_idx, new_status, worksheet_name="readdy_forms", credentials_file="credentials.json"):
    """
    特定行のステータスを更新する（Readdy連携完了後に 'done' 等へ更新するために使用）
    """
    try:
        sheet = init_readdy_sheet(spreadsheet_id, worksheet_name, credentials_file)
        mapping = get_column_mapping(sheet)
        status_col_idx = mapping.get("status")
        if status_col_idx is None:
            print("  ❌ status列が見つかりません。")
            return False
        status_col = chr(ord('A') + status_col_idx)
        sheet.update_acell(f"{status_col}{row_idx}", new_status)
        print(f"  -> 行 {row_idx} のステータスを '{new_status}' に更新しました。")
        return True
    except Exception as e:
        print(f"  ❌ ステータス更新中にエラー: {e}")
        return False