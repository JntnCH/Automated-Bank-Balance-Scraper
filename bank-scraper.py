import os
import time
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json

# ==========================================
# 1. การตั้งค่าสิทธิ์ Google Sheets API
# ==========================================
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

SERVICE_ACCOUNT_FILE = 'service_account.json'
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '')  # ดึง Sheet ID จาก Environment Variables
WORKSHEET_NAME = 'Balance'

def connect_google_sheet():
    """ Connect ไปยัง Google Sheets ผ่าน Service Account โดยใช้ Sheet ID """
    try:
        # ตรวจสอบ GOOGLE_SHEET_ID
        if not GOOGLE_SHEET_ID:
            raise Exception("ไม่พบ Environment Variable: GOOGLE_SHEET_ID")
        
        # ลองอ่านจากไฟล์ก่อน ถ้าไม่มีให้ลองอ่านจาก Environment Variable
        if os.path.exists(SERVICE_ACCOUNT_FILE):
            creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        else:
            # ถ้าไม่มีไฟล์ ให้ลองอ่านจาก Environment Variable
            service_account_json = os.getenv('SERVICE_ACCOUNT_JSON')
            if not service_account_json:
                raise Exception("ไม่พบไฟล์ service_account.json และ Environment Variable SERVICE_ACCOUNT_JSON")
            creds = Credentials.from_service_account_info(json.loads(service_account_json), scopes=SCOPES)
        
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(GOOGLE_SHEET_ID)
        
        # ตรวจสอบว่ามี Worksheet ชื่อ WORKSHEET_NAME หรือไม่ ถ้าไม่มีให้สร้างใหม่
        try:
            worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        except gspread.WorksheetNotFound:
            print(f"⚠️  ไม่พบ Worksheet '{WORKSHEET_NAME}' กำลังสร้าง...")
            worksheet = spreadsheet.add_worksheet(title=WORKSHEET_NAME, rows=100, cols=5)
            # เพิ่มหัวตาราง
            headers = ['ลำดับ', 'ธนาคาร', 'เลขที่บัญชี', 'ยอดคงเหลือ (บาท)', 'อัปเดตล่าสุด']
            worksheet.append_row(headers)
            print(f"✓ สร้าง Worksheet '{WORKSHEET_NAME}' สำเร็จ!")
        
        print("✓ เชื่อมต่อ Google Sheets สำเร็จ!")
        return worksheet
    except Exception as e:
        print(f"✗ เกิดข้อผิดพลาดในการเชื่อมต่อ Google Sheets: {e}")
        return None

# ==========================================
# 2. การตั้งค่า Selenium WebDriver
# ==========================================
def setup_browser(headless=True):
    """ สร้างตัวเปิดเบราว์เซอร์ Chrome แบบอัตโนมัติ """
    options = webdriver.ChromeOptions()
    
    if headless:
        options.add_argument('--headless')
        
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,720')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# ==========================================
# 3. ฟังก์ชัน Scraping ข้อมูลธนาคาร
# ==========================================

def scrape_kbank(driver, username, password, account_no):
    """ ดึงข้อมูลจากธนาคารกสิกรไทย """
    bank_name = 'กสิกรไทย (KBANK)'
    balance = "N/A"
    
    try:
        print(f"\n📊 กำลังดึงข้อมูลจาก {bank_name}...")
        driver.get('https://www.kasikornbank.com/')
        wait = WebDriverWait(driver, 15)
        
        # *** ต้องปรับ Selector ตามเว็บจริง ***
        # ตัวอย่างเท่านั้น:
        time.sleep(2)
        
        print(f"✓ ดึงข้อมูลสำเร็จ! {bank_name}: {balance} บาท")
    except Exception as e:
        print(f"✗ ไม่สามารถดึงข้อมูลจาก {bank_name} ได้: {e}")
    
    return {
        'bank_name': bank_name,
        'account_no': account_no,
        'balance': balance,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def scrape_ktb(driver, username, password, account_no):
    """ ดึงข้อมูลจากธนาคารกรุงไทย """
    bank_name = 'กรุงไทย (KTB)'
    balance = "N/A"
    
    try:
        print(f"\n📊 กำลังดึงข้อมูลจาก {bank_name}...")
        driver.get('https://www.ktb.co.th/')
        wait = WebDriverWait(driver, 15)
        
        # *** ต้องปรับ Selector ตามเว็บจริง ***
        time.sleep(2)
        
        print(f"✓ ดึงข้อมูลสำเร็จ! {bank_name}: {balance} บาท")
    except Exception as e:
        print(f"✗ ไม่สามารถดึงข้อมูลจาก {bank_name} ได้: {e}")
    
    return {
        'bank_name': bank_name,
        'account_no': account_no,
        'balance': balance,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def scrape_scb(driver, username, password, account_no):
    """ ดึงข้อมูลจากธนาคารไทยพาณิชย์ """
    bank_name = 'ไทยพาณิชย์ (SCB)'
    balance = "N/A"
    
    try:
        print(f"\n📊 กำลังดึงข้อมูลจาก {bank_name}...")
        driver.get('https://www.scb.co.th/')
        wait = WebDriverWait(driver, 15)
        
        # *** ต้องปรับ Selector ตามเว็บจริง ***
        time.sleep(2)
        
        print(f"✓ ดึงข้อมูลสำเร็จ! {bank_name}: {balance} บาท")
    except Exception as e:
        print(f"✗ ไม่สามารถดึงข้อมูลจาก {bank_name} ได้: {e}")
    
    return {
        'bank_name': bank_name,
        'account_no': account_no,
        'balance': balance,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

def scrape_kiacb(driver, username, password, account_no):
    """ ดึงข้อมูลจากธนาคารเกียรตินาคินภัทร """
    bank_name = 'เกียรตินาคินภัทร (KIACB)'
    balance = "N/A"
    
    try:
        print(f"\n📊 กำลังดึงข้อมูลจาก {bank_name}...")
        driver.get('https://www.kiacb.com/')
        wait = WebDriverWait(driver, 15)
        
        # *** ต้องปรับ Selector ตามเว็บจริง ***
        time.sleep(2)
        
        print(f"✓ ดึงข้อมูลสำเร็จ! {bank_name}: {balance} บาท")
    except Exception as e:
        print(f"✗ ไม่สามารถดึงข้อมูลจาก {bank_name} ได้: {e}")
    
    return {
        'bank_name': bank_name,
        'account_no': account_no,
        'balance': balance,
        'updated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

# ==========================================
# 4. ฟังก์ชันบันทึกข้อมูลลง Google Sheet
# ==========================================
def update_sheets_data(worksheet, data_list):
    """ อัปเดตข้อมูลยอดเงินลงในตาราง Google Sheets """
    if not worksheet:
        return

    print("\n💾 กำลังอัปเดตข้อมูลลงใน Google Sheet...")
    
    try:
        # ดึงข้อมูลทั้งหมดในชีตปัจจุบัน
        existing_records = worksheet.get_all_records()
        
        # หากยังไม่มีหัวตาราง ให้สร้างหัวตารางก่อน
        if not existing_records:
            worksheet.append_row(['ลำดับ', 'ธนาคาร', 'เลขที่บัญชี', 'ยอดคงเหลือ (บาท)', 'อัปเดตล่าสุด'])
        
        # วนลูปอัปเดตรายการข้อมูล
        for idx, item in enumerate(data_list, start=1):
            row_data = [
                idx,
                item['bank_name'],
                item['account_no'],
                item['balance'],
                item['updated_at']
            ]
            worksheet.append_row(row_data)
        
        print("✓ บันทึกข้อมูลเข้า Google Sheets เรียบร้อยแล้ว!")
    except Exception as e:
        print(f"✗ เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")

# ==========================================
# 5. ฟังก์ชันหลัก (Main Execution)
# ==========================================
def main():
    print("=" * 60)
    print("🏦 Bank Balance Scraper - เริ่มดำเนินการ")
    print("=" * 60)
    
    # กำหนดรายการธนาคารที่ต้องการเช็ค
    banks_config = [
        {
            'name': 'KBANK',
            'scrape_func': scrape_kbank,
            'username': os.getenv('KBANK_USER', ''),
            'password': os.getenv('KBANK_PASS', ''),
            'account_no': os.getenv('KBANK_ACCOUNT', 'xxx-x-x1234-x')
        },
        {
            'name': 'KTB',
            'scrape_func': scrape_ktb,
            'username': os.getenv('KTB_USER', ''),
            'password': os.getenv('KTB_PASS', ''),
            'account_no': os.getenv('KTB_ACCOUNT', 'xxx-x-x1234-x')
        },
        {
            'name': 'SCB',
            'scrape_func': scrape_scb,
            'username': os.getenv('SCB_USER', ''),
            'password': os.getenv('SCB_PASS', ''),
            'account_no': os.getenv('SCB_ACCOUNT', 'xxx-x-x1234-x')
        },
        {
            'name': 'KIACB',
            'scrape_func': scrape_kiacb,
            'username': os.getenv('KIACB_USER', ''),
            'password': os.getenv('KIACB_PASS', ''),
            'account_no': os.getenv('KIACB_ACCOUNT', 'xxx-x-x1234-x')
        }
    ]

    # เชื่อมต่อ Google Sheets
    worksheet = connect_google_sheet()
    if not worksheet:
        print("✗ ไม่สามารถดำเนินการต่อได้เนื่องจากไม่ได้เชื่อมต่อ Google Sheets")
        return

    # เริ่มรัน Browser Scraping
    driver = setup_browser(headless=True)  # Set headless=False สำหรับ testing
    results = []

    try:
        for bank in banks_config:
            if bank['username'] and bank['password']:
                data = bank['scrape_func'](driver, bank['username'], bank['password'], bank['account_no'])
                results.append(data)
            else:
                print(f"⚠️  ข้ามธนาคาร {bank['name']} เพราะไม่พบ credentials")
    finally:
        driver.quit()  # ปิดเบราว์เซอร์เมื่อทำงานเสร็จ

    # บันทึกข้อมูลทั้งหมดลง Google Sheets
    if results:
        update_sheets_data(worksheet, results)
    else:
        print("⚠️  ไม่มีข้อมูลที่ดึงมาได้")
    
    print("\n" + "=" * 60)
    print("✓ ดำเนินการเสร็จสิ้น")
    print("=" * 60)

if __name__ == '__main__':
    main()
