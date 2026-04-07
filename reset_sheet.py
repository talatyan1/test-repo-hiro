import gspread

SPREADSHEET_ID = "1xALyErlbTB7P32gf8b4qq4JY70FYxnA7PPOiMvHIK6U"

def reset_status():
    gc = gspread.service_account(filename="credentials.json")
    sh = gc.open_by_key(SPREADSHEET_ID)
    sheet = sh.get_worksheet(0)
    
    # 直接インデックスを指定してみる (Headers: status=11, __flow_status__=18)
    sheet.update_cell(5, 11, "")
    sheet.update_cell(5, 18, "")
    sheet.update_cell(5, 17, "") # result_url
    print("Row 5 status and URL cleared (Force).")

if __name__ == "__main__":
    reset_status()
