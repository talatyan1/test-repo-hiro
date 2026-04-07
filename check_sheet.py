import gspread

SPREADSHEET_ID = "1xALyErlbTB7P32gf8b4qq4JY70FYxnA7PPOiMvHIK6U"

def check_sheet():
    gc = gspread.service_account(filename="credentials.json")
    sh = gc.open_by_key(SPREADSHEET_ID)
    sheet = sh.get_worksheet(0)
    
    headers = sheet.row_values(1)
    print("Headers:", headers)
    
    row5 = sheet.row_values(5)
    print("Row 5:", row5)
    
    data = sheet.get_all_records()
    print("Total records:", len(data))

if __name__ == "__main__":
    check_sheet()
