import os
import time
import random
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# ==========================================
# CONFIGURATION
# ==========================================
CHROME_BETA_PATH = r"C:\Program Files\Google\Chrome Beta\Application\chrome.exe"
BASE_SEARCH_PATH = r"C:\Users\MR.SAKURA_Z\Downloads\Khomesolution\output\research"
CHATGPT_URL = "https://chatgpt.com/"
AUTH_FILE = "auth_state.json"

# Selectors
SELECTOR_TEXTAREA = "#prompt-textarea"
SELECTOR_SEND_READY = 'button[data-testid="send-button"]:not([disabled])'
SELECTOR_RESPONSE_BUBBLE = "div.markdown"

class ChatGPTResearcher:
    def __init__(self, headless: bool = False):
        self.playwright = sync_playwright().start()
        print(f"Initializing Playwright...")
        
        if not os.path.exists(CHROME_BETA_PATH):
            print(f"Error: Chrome Beta not found at {CHROME_BETA_PATH}")
            exit(1)

        self.browser = self.playwright.chromium.launch(
            executable_path=CHROME_BETA_PATH,
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-first-run",
                "--no-default-browser-check",
            ]
        )
        
        context_args = {"viewport": {"width": 1280, "height": 850}}
        if os.path.exists(AUTH_FILE):
            print(f"Loading session from {AUTH_FILE}...")
            context_args["storage_state"] = AUTH_FILE

        self.browser_context = self.browser.new_context(**context_args)
        self.browser_context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        
        self.page = self.browser_context.new_page()
        self.page.set_default_timeout(60000)
        print("Browser launched.")

    def navigate_home(self):
        print(f"Navigating to {CHATGPT_URL}...")
        self.page.goto(CHATGPT_URL, wait_until="domcontentloaded")
        
        if "auth/login" in self.page.url:
            print("⚠️ Please login manually...")
            self.page.wait_for_url("**/c/*", timeout=300000) 
            self.browser_context.storage_state(path=AUTH_FILE)

        try:
            self.page.wait_for_selector(SELECTOR_TEXTAREA, state="visible", timeout=30000)
            print("✅ Ready to chat.")
        except:
            print("❌ Error: Input box not found. Retrying navigation...")
            self.page.reload()
            self.page.wait_for_selector(SELECTOR_TEXTAREA, state="visible", timeout=30000)

    def perform_deep_research(self, keyword: str):
        target_dir = Path(BASE_SEARCH_PATH) / keyword
        if not target_dir.exists(): return False
        
        extensions = ['*.md', '*.pdf', '*.txt', '*.docx']
        files_to_upload = []
        for ext in extensions: files_to_upload.extend(target_dir.glob(ext))
        file_paths = [str(p) for p in files_to_upload]
        if not file_paths: return False

        print(f"🤖 Activating Deep Research for '{keyword}'...")

        # ==============================================================================
        # STEP 1: หาและกดปุ่ม (+)
        # ==============================================================================
        print("   1. 🔍 Locating (+) Button...")
        plus_button = None
        
        # Priority: หาปุ่ม Attach โดยตรง
        direct_selectors = [
            'button[aria-label="Attach files"]',
            'button[aria-label="แนบไฟล์"]',
            'button[aria-label="เพิ่มรูปภาพและไฟล์"]',
            'button[data-testid="attach-file-button"]'
        ]
        
        for sel in direct_selectors:
            if self.page.locator(sel).first.is_visible():
                plus_button = self.page.locator(sel).first
                print(f"      ✅ Found button: {sel}")
                break
        
        # Fallback: หาปุ่มข้างๆ Textarea
        if not plus_button:
            print("      ⚠️ Trying relative search...")
            try:
                candidates = self.page.locator('button').all()
                for btn in candidates:
                    if btn.is_visible() and btn.is_enabled():
                        label = (btn.get_attribute("aria-label") or "").lower()
                        if "attach" in label or "แนบ" in label or "เพิ่ม" in label:
                            plus_button = btn
                            break
            except: pass

        if not plus_button:
            print("❌ FATAL: (+) Button not found.")
            return False

        # กดปุ่ม (+)
        plus_button.click()
        time.sleep(1.0) # รอเมนูเด้ง (สำคัญ)

        # ==============================================================================
        # STEP 2: เลือกเมนู "การค้นคว้าเชิงลึก" (FIXED: Text Match Logic)
        # ==============================================================================
        print("   2. 👉 Selecting 'Deep Research'...")

        # ใช้ text search แทน selector (แม่นยำกว่า)
        # ลองหาคำว่า "การค้นคว้าเชิงลึก" หรือ "Deep Research" ในทั้งหน้า
        target_text_th = self.page.get_by_text("การค้นคว้าเชิงลึก", exact=False)
        target_text_en = self.page.get_by_text("Deep Research", exact=False)

        target_element = None

        try:
            if target_text_th.count() > 0 and target_text_th.first.is_visible():
                target_element = target_text_th.first
                print("      ✅ Found Thai text: 'การค้นคว้าเชิงลึก'")
            elif target_text_en.count() > 0 and target_text_en.first.is_visible():
                target_element = target_text_en.first
                print("      ✅ Found English text: 'Deep Research'")
            else:
                # ถ้าไม่เจอ ลองรอแป๊บนึงเผื่ออนิเมชั่น
                print("      ⏳ Waiting for menu text...")
                time.sleep(1)
                if target_text_th.count() > 0: target_element = target_text_th.first
                elif target_text_en.count() > 0: target_element = target_text_en.first

            if target_element:
                # กดที่ข้อความนั้นเลย
                target_element.click(force=True)
                print("      ✅ Clicked Deep Research menu.")
                time.sleep(3) # รอเปลี่ยนโหมด
            else:
                print("❌ ERROR: Menu opened but text 'การค้นคว้าเชิงลึก' NOT found.")
                print("      (Visible text on screen might be different?)")
                self.page.mouse.click(0, 0) # ปิดเมนู
                return False

        except Exception as e:
            print(f"❌ Error clicking menu: {e}")
            return False

        # ==============================================================================
        # STEP 3: อัปโหลดไฟล์
        # ==============================================================================
        print(f"   3. 📂 Uploading {len(file_paths)} files...")
        try:
            file_input = self.page.locator("input[type='file']").first
            file_input.set_input_files(file_paths)
            time.sleep(5) # รออัปโหลด
        except Exception as e:
            print(f"❌ Upload Failed: {e}")
            return False

        # ==============================================================================
        # STEP 4: กดส่ง
        # ==============================================================================
        send_btn = self.page.locator(SELECTOR_SEND_READY)
        if not send_btn.is_enabled():
            self.page.click(SELECTOR_TEXTAREA)
            self.page.keyboard.type(" ")
            time.sleep(1)

        if send_btn.is_enabled():
            send_btn.click()
            print("🚀 Prompt sent.")
        else:
            return False

        # ==============================================================================
        # STEP 5: ยืนยัน
        # ==============================================================================
        try:
            print("   4. Waiting for confirmation...")
            self.page.wait_for_selector(SELECTOR_SEND_READY, state="visible", timeout=60000)
            self.page.fill(SELECTOR_TEXTAREA, "ตกลง")
            time.sleep(1)
            btn = self.page.locator(SELECTOR_SEND_READY)
            if btn.is_enabled(): btn.click()
        except:
            pass

        return True

    def wait_for_completion(self, timeout_minutes=30) -> str:
        time.sleep(5) 
        try:
            print(f"⏳ Waiting for generation (Max {timeout_minutes} mins)...")
            self.page.wait_for_selector(SELECTOR_SEND_READY, timeout=timeout_minutes * 60000, state="visible")
            time.sleep(2)
            responses = self.page.query_selector_all(SELECTOR_RESPONSE_BUBBLE)
            return responses[-1].inner_text() if responses else ""
        except PlaywrightTimeoutError:
            print("❌ Timeout.")
            return ""

    def close(self):
        if os.path.exists(AUTH_FILE): self.browser_context.storage_state(path=AUTH_FILE)
        self.browser.close()
        self.playwright.stop()

# ==========================================
# MAIN
# ==========================================
def get_keywords(filepath):
    if not Path(filepath).exists(): return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip() and not l.startswith('#')]

def save_result(keyword, content, base_dir):
    path = base_dir / keyword / f"{keyword}-deep-research.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f: f.write(content)
    print(f"💾 Saved: {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", default="data/keywords/keywords.txt")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output-dir", default=r"C:\Users\MR.SAKURA_Z\Downloads\Khomesolution\output\research")
    parser.add_argument("--all", action="store_true")

    args = parser.parse_args()
    base_dir = Path(args.output_dir)
    keywords = get_keywords(args.keywords)
    
    print(f"Starting Pipeline for {len(keywords)} keywords.")
    bot = ChatGPTResearcher(headless=args.headless)
    
    try:
        for i, keyword in enumerate(keywords):
            print(f"\n--- Processing [{i+1}/{len(keywords)}]: {keyword} ---")
            if not getattr(args, 'all', False) and (base_dir / keyword / f"{keyword}-deep-research.md").exists():
                 print("Skipping: Already exists.")
                 continue

            try:
                bot.navigate_home()
                time.sleep(2)
                if bot.perform_deep_research(keyword):
                    res = bot.wait_for_completion(timeout_minutes=30)
                    if res: save_result(keyword, res, base_dir)
                else:
                    print("❌ Setup failed. Skipping.")
            except Exception as e:
                print(f"❌ Error: {e}")
                bot.page.reload()
                
    except KeyboardInterrupt:
        print("\n🛑 Interrupted.")
    finally:
        bot.close()