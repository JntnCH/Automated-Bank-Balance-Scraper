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

# ==========================================
# 1. การตั้งค่าสิทธิ์ Google Sheets API
# ==========================================
# กำหนด Scope ที่ต้องการใช้งานสำหรับ Google Sheets และ Google Drive
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# ชื่อไฟล์ Service Account Key (JSON) ที่ดาวน์โหลดมาจาก Google Cloud Console
SERVICE_ACCOUNT_FILE = 'service_account.json'

# ชื่อไฟล์ Google Sheet ที่ต้องการอัปเดตข้อมูล
SPREADSHEET_NAME = 'สรุปยอดเงินธนาคาร'
WORKSHEET_NAME = 'Balance'

def connect_google_sheet():
    """ Connect ไปยัง Google Sheets ผ่าน Service Account """
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SPREADSHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        print("เชื่อมต่อ Google Sheets สำเร็จ!")
        return worksheet
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการเชื่อมต่อ Google Sheets: {e}")
        return None

# ==========================================
# 2. การตั้งค่า Selenium WebDriver
# ==========================================
def setup_browser(headless=False):
    """ สร้างตัวเปิดเบราว์เซอร์ Chrome แบบอัตโนมัติ """
    options = webdriver.ChromeOptions()
    
    # หากต้องการให้รันแบบเบื้องหลัง (ไม่เปิดหน้าจอขึ้นมา) ให้ปลดล็อกบรรทัดล่าง
    if headless:
        options.add_argument('--headless')
        
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1280,720')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# ==========================================
# 3. ฟังก์ชัน Scraping ข้อมูลธนาคาร (ตัวอย่างโครงสร้าง)
# ==========================================
def scrape_bank_account(driver, bank_config):
    """
    ฟังก์ชันสำหรับล็อกอินและดึงยอดเงินจากเว็บธนาคาร
    หมายเหตุ: Selector (Xpath/ID) ต้องปรับเปลี่ยนตามโครงสร้างเว็บจริงของแต่ละธนาคาร
    """
    bank_name = bank_config['bank_name']
    url = bank_config['url']
    username = bank_config['username']
    password = bank_config['password']

    print(f"\nกำลังเริ่มดึงข้อมูลจากธนาคาร: {bank_name}...")
    balance = "N/A"
    account_no = bank_config['account_no']

    try:
        # เปิดหน้าเว็บธนาคาร
        driver.get(url)
        wait = WebDriverWait(driver, 15)

        # ----------------------------------------------------
        # ตัวอย่างขั้นตอนการกรอก Username และ Password
        # (หมายเหตุ: ID / Name ของ Element ต้องตรวจสอบจากเว็บจริง)
        # ----------------------------------------------------
        
        # 1. รอกรอก Username
        user_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        user_input.clear()
        user_input.send_keys(username)

        # 2. กรอก Password
        pass_input = driver.find_element(By.NAME, "password")
        pass_input.clear()
        pass_input.send_keys(password)

        # 3. กดปุ่ม Login
        login_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_btn.click()

        # 4. รอให้หน้าถัดไปโหลด และดึงข้อความยอดเงินคงเหลือ
        time.sleep(3) # รอนำเข้าข้อมูล
        balance_element = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "account-balance-amount"))
        )
        balance = balance_element.text.replace(',', '').strip()
        print(f"ดึงข้อมูลสำเร็จ! ยอดเงินคงเหลือ {bank_name}: {balance} บาท")

        # 5. สั่ง Logout เพื่อความปลอดภัย
        try:
            logout_btn = driver.find_element(By.LINK_TEXT, "ออกจากระบบ")
            logout_btn.click()
        except:
            pass

    except Exception as e:
        print(f"ไม่สามารถดึงข้อมูลจาก {bank_name} ได้: {e}")

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

    print("\nกำลังอัปเดตข้อมูลลงใน Google Sheet...")
    
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

    print("บันทึกข้อมูลเข้า Google Sheets เรียบร้อยแล้ว!")

# ==========================================
# 5. ฟังก์ชันหลัก (Main Execution)
# ==========================================
def main():
    # กำหนดรายการธนาคารที่ต้องการเช็ค (ดึงค่าจาก Environment Variables เพื่อความปลอดภัย)
    banks_to_scrape = [
        {
            'bank_name': 'ธนาคารกรุงเทพ (BBL)',
            'url': 'https://www.bangkokbank.com/', # URL ตัวอย่าง
            'username': os.getenv('BBL_USER', 'MY_USERNAME'),
            'password': os.getenv('BBL_PASS', 'MY_PASSWORD'),
            'account_no': 'xxx-x-x1234-x'
        },
        # สามารถเพิ่มธนาคารอื่นๆ ต่อท้ายได้ที่นี่
    ]

    # เชื่อมต่อ Google Sheets
    worksheet = connect_google_sheet()
    if not worksheet:
        print("ไม่สามารถดำเนินการต่อได้เนื่องจากไม่ได้เชื่อมต่อ Google Sheets")
        return

    # เริ่มรัน Browser Scraping
    driver = setup_browser(headless=False)
    results = []

    try:
        for bank in banks_to_scrape:
            data = scrape_bank_account(driver, bank)
            results.append(data)
    finally:
        driver.quit() # ปิดเบราว์เซอร์เมื่อทำงานเสร็จ

    # บันทึกข้อมูลทั้งหมดลง Google Sheets
    update_sheets_data(worksheet, results)

if __name__ == '__main__':
    main()