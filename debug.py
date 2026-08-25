import os
import json
from google.oauth2.service_account import Credentials
import gspread

# ==========================================
# Debug Script for Google Sheets Connection
# ==========================================

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SPREADSHEET_ID = os.getenv('GOOGLE_SHEET_ID', '')  # ดึงจาก Environment Variables
WORKSHEET_NAME = 'Balance'

def get_credentials():
    """Get credentials from environment variable or file"""
    try:
        # Try reading from file first
        if os.path.exists('service_account.json'):
            print("✓ พบไฟล์ service_account.json")
            creds = Credentials.from_service_account_file('service_account.json', scopes=SCOPES)
            return creds
        
        # Try from environment variable
        service_account_json = os.getenv('SERVICE_ACCOUNT_JSON')
        if not service_account_json:
            print("✗ ไม่พบ service_account.json และไม่พบ Environment Variable SERVICE_ACCOUNT_JSON")
            return None
        
        print("✓ ใช้ SERVICE_ACCOUNT_JSON จาก Environment Variable")
        creds = Credentials.from_service_account_info(json.loads(service_account_json), scopes=SCOPES)
        return creds
    except Exception as e:
        print(f"✗ เกิดข้อผิดพลาดในการอ่าน Credentials: {e}")
        return None

def get_or_create_worksheet(client, spreadsheet_id):
    """Get existing worksheet or create new one by Sheet ID"""
    try:
        if not spreadsheet_id:
            print("✗ ไม่พบ GOOGLE_SHEET_ID ใน Environment Variables")
            return None
        
        print(f"🔍 กำลังเปิด Spreadsheet จาก Sheet ID: {spreadsheet_id}...")
        spreadsheet = client.open_by_key(spreadsheet_id)
        print(f"✓ เปิด Spreadsheet สำเร็จ: '{spreadsheet.title}'")
        
        # Try to get existing worksheet
        print(f"🔍 กำลังค้นหา Worksheet: '{WORKSHEET_NAME}'...")
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        print(f"✓ พบ Worksheet: '{WORKSHEET_NAME}'")
        return worksheet
    except gspread.WorksheetNotFound:
        print(f"✗ ไม่พบ Worksheet: '{WORKSHEET_NAME}'")
        print(f"📝 กำลังสร้าง Worksheet ใหม่...")
        
        try:
            # Create new worksheet
            spreadsheet = client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=100, cols=5)
            print(f"✓ สร้าง Worksheet ใหม่สำเร็จ: '{WORKSHEET_NAME}'")
            
            # Add headers
            headers = ['ลำดับ', 'ธนาคาร', 'เลขที่บัญชี', 'ยอดคงเหลือ (บาท)', 'อัปเดตล่าสุด']
            worksheet.append_row(headers)
            print(f"✓ เพิ่มหัวตารางแล้ว")
            
            return worksheet
        except Exception as e:
            print(f"✗ ไม่สามารถสร้าง Worksheet: {e}")
            return None
    except gspread.SpreadsheetNotFound:
        print(f"✗ ไม่พบ Spreadsheet ด้วย Sheet ID: {spreadsheet_id}")
        print("💡 ตรวจสอบว่า Sheet ID ถูกต้องหรือไม่")
        return None
    except Exception as e:
        print(f"✗ เกิดข้อผิดพลาด: {e}")
        return None

def test_connection():
    """Test Google Sheets connection"""
    print("=" * 60)
    print("🧪 ทดสอบการเชื่อมต่อ Google Sheets (ใช้ Sheet ID)")
    print("=" * 60)
    
    # Step 1: Check if GOOGLE_SHEET_ID is set
    print("\n[Step 0] ตรวจสอบ GOOGLE_SHEET_ID...")
    if not SPREADSHEET_ID:
        print("✗ ไม่พบ Environment Variable: GOOGLE_SHEET_ID")
        print("💡 ตั้งค่า: export GOOGLE_SHEET_ID='your_sheet_id'")
        return False
    print(f"✓ พบ GOOGLE_SHEET_ID: {SPREADSHEET_ID}")
    
    # Step 1: Get credentials
    print("\n[Step 1] กำลังอ่าน Credentials...")
    creds = get_credentials()
    if not creds:
        print("\n✗ ไม่สามารถอ่าน Credentials")
        return False
    
    # Step 2: Authorize client
    print("\n[Step 2] กำลังเชื่อมต่อ Google Sheets API...")
    try:
        client = gspread.authorize(creds)
        print("✓ เชื่อมต่อ Google Sheets API สำเร็จ!")
    except Exception as e:
        print(f"✗ ไม่สามารถเชื่อมต่อ Google Sheets API: {e}")
        return False
    
    # Step 3: Get or create worksheet
    print("\n[Step 3] กำลังค้นหาหรือสร้าง Worksheet...")
    worksheet = get_or_create_worksheet(client, SPREADSHEET_ID)
    if not worksheet:
        return False
    
    # Step 4: Test write
    print("\n[Step 4] กำลังทดสอบการเขียนข้อมูล...")
    try:
        from datetime import datetime
        test_data = [
            1,
            'ทดสอบ (TEST)',
            'xxx-x-x0000-x',
            '0.00',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
        worksheet.append_row(test_data)
        print("✓ เขียนข้อมูลทดสอบสำเร็จ!")
    except Exception as e:
        print(f"✗ ไม่สามารถเขียนข้อมูล: {e}")
        return False
    
    # Step 5: Test read
    print("\n[Step 5] กำลังทดสอบการอ่านข้อมูล...")
    try:
        records = worksheet.get_all_records()
        print(f"✓ อ่านข้อมูลสำเร็จ! (พบ {len(records)} แถว)")
        if records:
            print(f"   ข้อมูลแถวสุดท้าย: {records[-1]}")
    except Exception as e:
        print(f"✗ ไม่สามารถอ่านข้อมูล: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ ทดสอบการเชื่อมต่อเสร็จสิ้น - ทุกอย่างถูกต้อง!")
    print("=" * 60)
    print(f"\n📊 Spreadsheet URL: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}")
    
    return True

if __name__ == '__main__':
    test_connection()
