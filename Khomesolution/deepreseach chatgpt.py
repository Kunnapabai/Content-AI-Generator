from playwright.sync_api import sync_playwright
import time
import os

# ================= CONFIGURATION =================

CHROME_PATH = r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe"
USER_DATA_DIR = r"C:\Users\MR.SAKURA_Z\AppData\Local\Google\Chrome Beta\User Data Test"
FILE_TO_UPLOAD = r"C:\Users\MR.SAKURA_Z\Downloads\MyModel\cookies.json"
DOWNLOAD_PATH = os.path.join(os.getcwd(), "research_output")

# 1. คำสั่งแรก: สั่งวิจัยอย่างเดียว (ห้ามพูดเรื่องไฟล์ เดี๋ยวบอทสับสน)
RESEARCH_TOPIC = """
[คำสั่งเริ่มงาน]
หัวข้อ: เจาะลึก https://flikover.com เครื่องมือ Data SEO
Scope:
1. วิเคราะห์ข้อมูลจากไฟล์ cookies.json ที่แนบไป
2. เปรียบเทียบฟีเจอร์กับ Official Tools และ Group Buy คู่แข่ง
3. วิเคราะห์ Reliability/Uptime/Reviews
4. สรุปความคุ้มค่า

สำคัญ: เริ่ม Deep Research ข้อมูลเชิงลึกทันที
"""

# 2. คำสั่งยืนยัน: ใช้ตอบเมื่อบอทถาม "จะให้ทำอะไรต่อ?" หรือ "ขอข้อมูลเพิ่ม"
CONFIRM_MSG = """
ดำเนินการต่อได้เลยครับ:
- ไม่ต้องถามรายละเอียดเพิ่ม
- ให้ครอบคลุมคู่แข่งทั้งหมดเท่าที่หาได้
- ลุย Research ให้จบกระบวนการ
"""

# 3. คำสั่งปิดท้าย: จะส่งเมื่อ Research เสร็จแล้วเท่านั้น
FINAL_MARKDOWN_CMD = """
การวิจัยเสร็จสิ้นแล้วใช่ไหม?
คำสั่งสุดท้าย: ให้นำผลลัพธ์การวิจัยทั้งหมด มารวมกันและสร้างเป็นไฟล์ "Markdown (.md)" ให้ฉันดาวน์โหลดเดี๋ยวนี้
"""

# =================================================

def robust_send_message(page, text):
    """ฟังก์ชันพิมพ์แบบแน่นหนา (แก้ปัญหาพิมพ์ไม่ติด)"""
    try:
        # รอให้ช่องแชทพร้อมใช้งานจริงๆ
        textarea = page.locator("#prompt-textarea")
        textarea.wait_for(state="visible", timeout=10000)
        
        # คลิกย้ำเพื่อให้ cursor focus
        textarea.click()
        time.sleep(0.5)
        
        # ล้างข้อความเก่า (ถ้ามี) แล้วพิมพ์ใหม่
        textarea.fill("") 
        textarea.fill(text)
        time.sleep(1)
        
        # กด Enter
        page.keyboard.press("Enter")
        
        # เช็คปุ่ม Send เผื่อต้องกดซ้ำ
        try:
            send_btn = page.locator('button[data-testid="send-button"]')
            if send_btn.is_visible(): send_btn.click()
        except: pass
        
        return True
    except Exception as e:
        print(f"   ⚠️ พิมพ์ข้อความไม่สำเร็จ: {e}")
        return False

def select_deep_research(page):
    print("🤖 กำลังเลือกโหมด Deep Research...")
    try:
        plus_btn = page.locator('button[data-testid="composer-attachment-button"]').first
        if not plus_btn.is_visible():
            plus_btn = page.locator('button[aria-label="Add attachments"], button[aria-label*="เพิ่ม"]').first
        
        if plus_btn.is_visible():
            plus_btn.click()
            time.sleep(1.5)
            target = page.get_by_text("การค้นคว้าเชิงลึก", exact=False)
            if not target.is_visible(): target = page.get_by_text("Deep Research", exact=False)
            if target.is_visible():
                target.click()
                print("   ✅ เลือกโหมดสำเร็จ")
                return True
            page.keyboard.press("ArrowDown"); page.keyboard.press("ArrowDown"); page.keyboard.press("Enter")
            return True
    except: pass
    return False

def upload_file(page, file_path):
    print(f"📂 กำลังอัปโหลดไฟล์: {os.path.basename(file_path)}")
    try:
        if not os.path.exists(file_path):
            print(f"   ❌ ไม่พบไฟล์: {file_path}")
            return False
        page.set_input_files("input[type='file']", file_path)
        time.sleep(3) 
        print("   ✅ อัปโหลดไฟล์เสร็จสิ้น")
        return True
    except: return False

def run():
    if not os.path.exists(DOWNLOAD_PATH): os.makedirs(DOWNLOAD_PATH)

    print("🚀 Opening Chrome Beta...")
    with sync_playwright() as p:
        try:
            context = p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                executable_path=CHROME_PATH,
                headless=False,
                slow_mo=50,
                args=["--start-maximized", "--disable-blink-features=AutomationControlled"],
                viewport=None 
            )
            page = context.pages[0]
            page.goto("https://chatgpt.com/", timeout=0)
            
            # รอโหลดหน้าเว็บให้เสร็จจริงจัง
            try: page.wait_for_selector("#prompt-textarea", state="visible", timeout=15000)
            except: pass
            
        except Exception as e:
            print(f"❌ Error: {e}"); return

        time.sleep(3)
        select_deep_research(page)
        upload_file(page, FILE_TO_UPLOAD)

        # -----------------------------------------------------------
        # STEP 1: ส่งคำสั่งเริ่มงาน (Research Topic)
        # -----------------------------------------------------------
        print(f"✍️ ส่งคำสั่งเริ่มงาน (Research Only)...")
        if not robust_send_message(page, RESEARCH_TOPIC):
            print("❌ พิมพ์ไม่ได้ โปรแกรมหยุดทำงาน"); return

        print("\n⏳ เข้าสู่โหมดเฝ้าระวัง (Smart Logic)...")
        
        start_time = time.time()
        timeout = 3600 
        has_sent_final_cmd = False # ตัวแปรเช็คว่าส่งคำสั่งขอไฟล์ไปหรือยัง
        
        while (time.time() - start_time) < timeout:
            if page.is_closed(): break

            # A. เช็คปุ่ม Download (ถ้ามีคือกดเลย จบงาน)
            download_btn = page.locator("button:has-text('Download'), [aria-label*='Download'], a:has-text('Download')").last
            if download_btn.is_visible():
                print("\n🎉 งานเสร็จสมบูรณ์! เจอปุ่ม Download")
                time.sleep(2)
                try:
                    with page.expect_download(timeout=60000) as download_info:
                        download_btn.click()
                    save_path = os.path.join(DOWNLOAD_PATH, f"Flikover_Research_{int(time.time())}.md")
                    download_info.value.save_as(save_path)
                    print(f"✅ Downloaded: {save_path}")
                    os.startfile(DOWNLOAD_PATH)
                except Exception as e: print(f"❌ Download Error: {e}")
                print("👋 จบการทำงาน"); break 

            # B. เช็คสถานะการพิมพ์ (Input Box vs Stop Button)
            input_box = page.locator("#prompt-textarea")
            stop_btn = page.locator('button[aria-label="Stop generating"], button[data-testid="stop-button"]')
            
            # ถ้าช่องพิมพ์โผล่มา และ ไม่มีปุ่ม Stop (แปลว่าบอทหยุดรอเรา)
            if input_box.is_visible() and not stop_btn.is_visible():
                
                # อ่านข้อความล่าสุดของบอท
                try:
                    msgs = page.locator('div[data-message-author-role="assistant"]')
                    if msgs.count() > 0:
                        last_msg = msgs.last.inner_text().lower()
                    else:
                        last_msg = ""
                except: last_msg = ""

                # เช็คว่าเป็นคำถามหรือไม่? (?, confirm, option, choose)
                is_question = any(k in last_msg for k in ["?", "ไหม", "เลือก", "confirm", "specify"])

                # --- LOGIC ตัดสินใจ ---
                
                if not has_sent_final_cmd:
                    if is_question:
                        # 1. บอทถาม -> ตอบยืนยัน (Confirm)
                        print(f"\n🤔 บอทถามคำถาม... ตอบกลับ: 'ลุยต่อเลย'")
                        robust_send_message(page, CONFIRM_MSG)
                        time.sleep(5)
                    else:
                        # 2. บอทไม่ถาม & นิ่งแล้ว -> แปลว่าวิจัยเสร็จ -> สั่งทำไฟล์ (Final Command)
                        print(f"\n🏁 Research น่าจะเสร็จแล้ว (ไม่เจอคำถาม)")
                        print("👉 ส่งคำสั่งสุดท้าย: สร้างไฟล์ Markdown เดี๋ยวนี้!")
                        robust_send_message(page, FINAL_MARKDOWN_CMD)
                        has_sent_final_cmd = True # ล็อกไว้ว่าสั่งไปแล้ว จะได้ไม่สั่งซ้ำ
                        time.sleep(5)
                
                else:
                    # 3. สั่งทำไฟล์ไปแล้ว -> รอ Loop รอบหน้าเพื่อหาปุ่ม Download
                    pass

            time.sleep(2)

        time.sleep(3)
        context.close()

if __name__ == "__main__":
    run()