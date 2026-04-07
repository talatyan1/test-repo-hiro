import pandas as pd
from pathlib import Path
import shutil
from src.config import Config
from src.logger import app_logger, error_logger

class ExcelReader:
    def __init__(self):
        self.input_dir = Config.INPUT_DIR
        self.archive_dir = Config.ARCHIVE_DIR

    def get_pending_files(self) -> list[Path]:
        """
        処理待ちのExcelファイル一覧を取得します
        """
        return list(self.input_dir.glob("*.xlsx"))

    def read_jobs(self, file_path: Path) -> list[dict]:
        """
        Excelファイルを読み込み、案件データのリストを返します。
        出力例:
        [
            {
                "site": "crowdworks",
                "title": "LPデザイン制作",
                "url": "https://...",
                ...
            }
        ]
        """
        try:
            # pandasでExcelを読み込む (1行目がヘッダーであると想定)
            df = pd.read_excel(file_path)
            
            # DataFrameを辞書のリストに変換
            records = df.to_dict('records')
            
            jobs = []
            for row in records:
                # 辞書のキー(Excelのヘッダー名)が異なる可能性があるため、マッピング処理
                # ※ここは実際のExcelの列名・フォーマットに合わせて調整する必要があります
                
                # 日本語の列名などから、システムで使う標準的なキー(title, url, etc.)へ変換
                job_data = {
                    # デフォルトで file名（あるいは内容）からサイトを推測
                    "site": self._guess_site(file_path, row),
                    "title": str(row.get("タイトル", row.get("title", ""))),
                    "url": str(row.get("URL", row.get("url", ""))),
                    "reward": str(row.get("報酬", row.get("予算", row.get("reward", "")))),
                    "description": str(row.get("内容", row.get("詳細", row.get("description", "")))),
                    "deadline": str(row.get("期限", row.get("応募期限", row.get("deadline", "")))),
                    "client_info": str(row.get("クライアント", row.get("発注者", "")))
                }
                jobs.append(job_data)
                
            app_logger.info(f"{file_path.name} から {len(jobs)} 件の案件を読み込みました。")
            return jobs
            
        except Exception as e:
            error_logger.error(f"{file_path.name} の読み込みに失敗しました: {e}")
            return []

    def _guess_site(self, file_path: Path, row: dict) -> str:
        """
        ファイル名やURLから対象サイト(crowdworks, lancers, coconala)を推測します
        """
        name_lower = file_path.name.lower()
        url = str(row.get("URL", row.get("url", ""))).lower()
        
        if "crowdworks" in name_lower or "crowdworks" in url:
            return "crowdworks"
        elif "lancers" in name_lower or "lancers" in url:
            return "lancers"
        elif "coconala" in name_lower or "coconala" in url:
            return "coconala"
            
        return "unknown"

    def archive_file(self, file_path: Path):
        """
        処理が完了したExcelファイルをアーカイブフォルダに移動します
        """
        try:
            dest = self.archive_dir / file_path.name
            shutil.move(str(file_path), str(dest))
            app_logger.info(f"{file_path.name} をアーカイブしました。")
        except Exception as e:
            error_logger.error(f"{file_path.name} のアーカイブに失敗しました: {e}")
