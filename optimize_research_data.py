import os
import time
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright
from concurrent.futures import ThreadPoolExecutor # <--- เพิ่มตัวช่วยรันหลายจอ

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
    # ปรับ __init__ ให้รับค่า config
    def __init__(self, headless: bool = False, poll_interval: int = 60, deep_timeout: int = 40, debug_port: int = 0):
        self.poll_interval = poll_interval
        self.deep_timeout = deep_timeout
        
        print(f"Initializing Playwright (Port: {debug_port})...")
        self.playwright = sync_playwright().start()
        
        if not os.path.exists(CHROME_BETA_PATH):
            print(f"Error: Chrome Beta not found at {CHROME_BETA_PATH}")
            exit(1)

        launch_args = [
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        
        # เพิ่ม Logic สำหรับ debug-port
        if debug_port > 0:
            launch_args.append(f"--remote-debugging-port={debug_port}")

        self.browser = self.playwright.chromium.launch(
            executable_path=CHROME_BETA_PATH,
            headless=headless,
            args=launch_args
        )
        
        context_args = {
            "viewport": {"width": 1280, "height": 850},
            "accept_downloads": True
        }
        if os.path.exists(AUTH_FILE):
            # print(f"Loading session from {AUTH_FILE}...") # ปิด print ลดรกหน้าจอ
            context_args["storage_state"] = AUTH_FILE

        self.context = self.browser.new_context(**context_args)
        self.context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")

    def run_keyword_task(self, keyword: str):
        target_dir = Path(BASE_SEARCH_PATH) / keyword
        
        # ค้นหาไฟล์ Prompt
        target_file = None
        for ext in ['.md', '.txt', '.docx', '.pdf']:
            check_path = target_dir / f"{keyword}-research-prompt{ext}"
            if check_path.exists():
                target_file = str(check_path)
                break
        
        if not target_file:
            print(f"❌ [{keyword}] Skipped: File prompt not found.")
            return False

        print(f"\n🚀 [{keyword}] Starting Task...")

        page = self.context.new_page()
        page.set_default_timeout(60000)

        try:
            page.goto(CHATGPT_URL, wait_until="domcontentloaded")
            
            if "auth/login" in page.url:
                print(f"⚠️ [{keyword}] Not logged in.")
                page.close()
                return False

            # รอ Input Box
            try:
                page.wait_for_selector(SELECTOR_TEXTAREA, state="visible", timeout=30000)
            except:
                page.reload()
                page.wait_for_selector(SELECTOR_TEXTAREA, state="visible", timeout=30000)

            # 1. กดปุ่ม (+)
            plus_button = None
            selectors = [
                'button[aria-label="Attach files"]',
                'button[aria-label="แนบไฟล์"]',
                'button[aria-label="เพิ่มรูปภาพและไฟล์"]',
                'button[data-testid="attach-file-button"]'
            ]
            for sel in selectors:
                if page.locator(sel).first.is_visible():
                    plus_button = page.locator(sel).first
                    break
            
            if not plus_button:
                # Fallback
                btns = page.locator('button').all()
                for btn in btns:
                    if btn.is_visible():
                        label = (btn.get_attribute("aria-label") or "").lower()
                        if "attach" in label or "แนบ" in label or "เพิ่ม" in label:
                            plus_button = btn
                            break
            
            if not plus_button:
                print(f"❌ [{keyword}] Button (+) not found.")
                page.close()
                return False

            plus_button.click()
            time.sleep(1.5)

            # 2. เลือก Deep Research
            try:
                page.wait_for_selector('div[role="menuitem"]', timeout=3000)
            except:
                plus_button.click()
                time.sleep(1)

            target_el = None
            if page.get_by_text("การค้นคว้าเชิงลึก").count() > 0:
                target_el = page.get_by_text("การค้นคว้าเชิงลึก").first
            elif page.get_by_text("Deep Research").count() > 0:
                target_el = page.get_by_text("Deep Research").first

            if target_el and target_el.is_visible():
                target_el.click(force=True)
                time.sleep(2)
            else:
                print(f"❌ [{keyword}] Deep Research menu missing.")
                page.close()
                return False

            # 3. อัปโหลด
            try:
                file_input = page.locator("input[type='file']").first
                file_input.set_input_files([target_file]) 
                time.sleep(5)
            except Exception as e:
                print(f"❌ [{keyword}] Upload Error: {e}")
                page.close()
                return False

            # 4. กดส่ง
            send_btn = page.locator(SELECTOR_SEND_READY)
            if not send_btn.is_enabled():
                page.click(SELECTOR_TEXTAREA)
                page.keyboard.type(" ")
                time.sleep(1)

            if send_btn.is_enabled():
                send_btn.click()
                print(f"🚀 [{keyword}] Prompt sent. Monitoring...")
            else:
                page.close()
                return False

            # 5. Monitor (ส่ง keyword เข้าไปเพื่อใช้ใน log)
            success = self.monitor_and_download(page, keyword)
            page.close()
            return success

        except Exception as e:
            print(f"❌ [{keyword}] Error: {e}")
            page.close()
            return False

    def monitor_and_download(self, page, keyword):
        # ใช้ค่าจาก self.deep_timeout และ self.poll_interval
        target_dir = Path(BASE_SEARCH_PATH) / keyword
        final_file_path = target_dir / f"{keyword}-research.md"
        
        start_time = time.time()
        timeout_seconds = self.deep_timeout * 60
        last_action_time = 0
        
        while (time.time() - start_time) < timeout_seconds:
            try:
                send_btn = page.locator(SELECTOR_SEND_READY)
                
                if send_btn.is_visible() and send_btn.is_enabled():
                    bubbles = page.locator(SELECTOR_RESPONSE_BUBBLE).all()
                    last_text = bubbles[-1].inner_text() if bubbles else ""
                    last_text_len = len(last_text)
                    
                    if last_text_len < 2000:
                        if (time.time() - last_action_time) > 10:
                            print(f"❓ [{keyword}] Bot paused. Replying 'Yes'...")
                            page.fill(SELECTOR_TEXTAREA, "Yes, please proceed.")
                            time.sleep(1)
                            page.click(SELECTOR_SEND_READY)
                            last_action_time = time.time()
                            time.sleep(10)
                        else:
                            time.sleep(2)
                            continue
                    else:
                        print(f"🎉 [{keyword}] Content detected. Downloading...")
                        page.fill(SELECTOR_TEXTAREA, "Create downloadable Markdown file now")
                        time.sleep(1)
                        page.click(SELECTOR_SEND_READY)
                        return self._download_file(page, final_file_path, keyword)

                # ใช้ self.poll_interval แทนการ sleep(5)
                time.sleep(self.poll_interval)
                
            except Exception as e:
                time.sleep(5)
        
        print(f"⏰ [{keyword}] Timeout reached.")
        return False

    def _download_file(self, page, save_path, keyword):
        try:
            with page.expect_download(timeout=180000) as download_info:
                page.wait_for_selector(SELECTOR_SEND_READY, timeout=120000)
                btn = page.locator('button[aria-label="Download"], div[role="button"]:has-text("Download"), a[download]').last
                if not btn.is_visible():
                     btn = page.locator('.markdown button, .markdown a').filter(has_text="Download").last
                
                if btn.is_visible():
                    btn.click()
                else:
                    return False

            download = download_info.value
            download.save_as(save_path)
            print(f"💾 [{keyword}] Saved: {save_path}")
            return True
        except Exception as e:
            print(f"❌ [{keyword}] Download failed: {e}")
            return False

    def close(self):
        if os.path.exists(AUTH_FILE):
             self.context.storage_state(path=AUTH_FILE)
        self.browser.close()
        self.playwright.stop()

# ==========================================
# MAIN EXECUTION (MODIFIED)
# ==========================================
def get_keywords(filepath):
    if not Path(filepath).exists(): return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip() and not l.startswith('#')]

# ฟังก์ชัน Worker สำหรับรัน 1 Keyword (สร้าง Bot ใหม่ทุกครั้งเพื่อให้ Thread-safe)
def worker_task(args_tuple):
    keyword, config = args_tuple
    
    # ถ้า debug-port ถูกเซ็ต และรันหลายจอพร้อมกัน ต้องระวังพอร์ตชนกัน
    # Code นี้จะยอมให้ใช้ port เดิม (ซึ่ง Playwright อาจจะ error ถ้าเปิดหลายจอ)
    # แนะนำ: ถ้า max-active > 1 อย่าใส่ debug-port หรือใส่ 0
    port_to_use = config.debug_port if config.max_active == 1 else 0

    bot = ChatGPTResearcher(
        headless=config.headless, 
        poll_interval=config.poll_interval,
        deep_timeout=config.deep_timeout,
        debug_port=port_to_use
    )
    
    try:
        bot.run_keyword_task(keyword)
    except Exception as e:
        print(f"💥 Critical Error on {keyword}: {e}")
    finally:
        bot.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", default="data/keywords/keywords.txt")
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--output-dir", default=r"C:\Users\MR.SAKURA_Z\Downloads\Khomesolution\output\research")
    parser.add_argument("--all", action="store_true")
    
    # เพิ่ม Arguments ใหม่ที่คุณต้องการ
    parser.add_argument("--max-active", type=int, default=1, help="Number of concurrent browsers")
    parser.add_argument("--poll-interval", type=int, default=5, help="Seconds to wait between checks")
    parser.add_argument("--deep-timeout", type=int, default=60, help="Minutes to wait for research")
    parser.add_argument("--debug-port", type=int, default=0, help="Chrome remote debugging port (Works best with max-active=1)")

    args = parser.parse_args()
    base_dir = Path(args.output_dir)
    keywords = get_keywords(args.keywords)
    
    # Filter keywords (Logic เดิม)
    tasks = []
    for keyword in keywords:
        final_path = base_dir / keyword / f"{keyword}-research.md"
        if not getattr(args, 'all', False) and final_path.exists():
            print(f"Skipping '{keyword}': Done.")
            continue
        tasks.append((keyword, args))

    print(f"Starting Task for {len(tasks)} keywords with {args.max_active} concurrent workers.")
    
    

    # ใช้ ThreadPoolExecutor แทน Loop ปกติ
    if tasks:
        with ThreadPoolExecutor(max_workers=args.max_active) as executor:
            executor.map(worker_task, tasks)
            
    print("\n🏁 All tasks finished.")