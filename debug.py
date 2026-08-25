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

SPREADSHEET_NAME = 'สรุปยอดเงินธนาคาร'
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

def get_or_create_spreadsheet(client):
    """Get existing spreadsheet or create new one"""
    try:
        # Try to open existing spreadsheet
        print(f"🔍 กำลังค้นหา Spreadsheet: '{SPREADSHEET_NAME}'...")
        spreadsheet = client.open(SPREADSHEET_NAME)
        print(f"✓ พบ Spreadsheet: '{SPREADSHEET_NAME}'")
        return spreadsheet
    except gspread.SpreadsheetNotFound:
        print(f"✗ ไม่พบ Spreadsheet: '{SPREADSHEET_NAME}'")
        print(f"📝 กำลังสร้าง Spreadsheet ใหม่...")
        
        try:
            # Create new spreadsheet
            spreadsheet = client.create(SPREADSHEET_NAME)
            print(f"✓ สร้าง Spreadsheet ใหม่สำเร็จ: '{SPREADSHEET_NAME}'")
            
            # Share with service account email (optional)
            try:
                creds_dict = json.loads(os.getenv('SERVICE_ACCOUNT_JSON', '{}'))
                if not os.path.exists('service_account.json'):
                    service_account_email = creds_dict.get('client_email', '')
                    if service_account_email:
                        print(f"📧 Service Account Email: {service_account_email}")
                        print(f"⚠️  ตรวจสอบว่า Google Sheets ได้รับ Editor access แล้ว")
            except:
                pass
            
            return spreadsheet
        except Exception as e:
            print(f"✗ ไม่สามารถสร้าง Spreadsheet: {e}")
            return None

def get_or_create_worksheet(spreadsheet):
    """Get existing worksheet or create new one"""
    try:
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

def test_connection():
    """Test Google Sheets connection"""
    print("=" * 60)
    print("🧪 ทดสอบการเชื่อมต่อ Google Sheets")
    print("=" * 60)
    
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
    
    # Step 3: Get or create spreadsheet
    print("\n[Step 3] กำลังค้นหาหรือสร้าง Spreadsheet...")
    spreadsheet = get_or_create_spreadsheet(client)
    if not spreadsheet:
        return False
    
    # Step 4: Get or create worksheet
    print("\n[Step 4] กำลังค้นหาหรือสร้าง Worksheet...")
    worksheet = get_or_create_worksheet(spreadsheet)
    if not worksheet:
        return False
    
    # Step 5: Test write
    print("\n[Step 5] กำลังทดสอบการเขียนข้อมูล...")
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
    
    # Step 6: Test read
    print("\n[Step 6] กำลังทดสอบการอ่านข้อมูล...")
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
    print(f"\n📊 Spreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
    
    return True

if __name__ == '__main__':
    test_connection()
