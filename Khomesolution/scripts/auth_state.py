from playwright.sync_api import sync_playwright
import time
import os

AUTH_FILE = "auth_state.json"
CHATGPT_URL = "https://chatgpt.com/"
# ตรวจสอบ Path ให้แน่ใจว่าไฟล์อยู่ที่นี่จริง
CHROME_BETA_PATH = r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe"

def run():
    with sync_playwright() as p:
        print("🚀 Launching Chrome Beta...")
        
        browser = p.chromium.launch(
            executable_path=CHROME_BETA_PATH,
            headless=False,
            # เพิ่ม args เหล่านี้เพื่อหลบการตรวจจับของ Cloudflare/OpenAI
            args=[
                "--disable-blink-features=AutomationControlled", 
                "--no-sandbox",
                "--disable-infobars"
            ]
        )

        # สร้าง Context พร้อมระบุ User Agent ให้เหมือนคนจริง
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        
        page = context.new_page()

        # ป้องกันการตรวจจับเพิ่มเติมโดยการลบ webdriver property
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        try:
            print(f"🔗 Going to {CHATGPT_URL}")
            page.goto(CHATGPT_URL)

            print("\n" + "="*50)
            print("👉 กรุณา Login ด้วยตัวเองในหน้าต่าง Chrome ที่เด้งขึ้นมา")
            print("👉 เมื่อ Login เสร็จและเห็นหน้าแชทแล้ว ให้กลับมาที่นี่แล้วกด Enter")
            print("="*50 + "\n")
            
            input("Press Enter to save cookies...")

            # Save cookies + localStorage
            context.storage_state(path=AUTH_FILE)
            print(f"✅ บันทึก Session ไว้ที่ไฟล์: {os.path.abspath(AUTH_FILE)}")

        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            browser.close()
            print("👋 Browser closed.")

if __name__ == "__main__":
    run()