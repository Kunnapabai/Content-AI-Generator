import os
import json
import time
import base64
import re
import requests
import random
import pandas as pd
from urllib.parse import urlparse, quote, unquote
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# ================= ⚙️ CONFIG (ตั้งค่า) =================

# 1. ระบุตำแหน่งไฟล์ User & Password.env
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, "..", "User & Password.env")

# 2. โหลดไฟล์ .env
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded config from: {env_path}")
else:
    load_dotenv("User & Password.env")
    print("⚠️ Trying to load config from current directory...")

# 3. ดึงค่าตัวแปร
LOGIN_URL = os.getenv("FLIKOVER_LOGIN_URL")
EMAIL = os.getenv("FLIKOVER_EMAIL")
PASSWORD = os.getenv("FLIKOVER_PASSWORD")

# 4. ตรวจสอบค่า (Debug Mode)
print(f"   🔎 Check Variables:")
print(f"      - EMAIL: {'✅ Found' if EMAIL else '❌ Missing'}")
print(f"      - PASSWORD: {'✅ Found' if PASSWORD else '❌ Missing'}")
print(f"      - LOGIN_URL: {'✅ Found' if LOGIN_URL else '❌ Missing'}")

if not LOGIN_URL or not EMAIL or not PASSWORD:
    print("\n❌ Error: ค่า Config ไม่ครบ!")
    print(f"   กรุณาเปิดไฟล์: {env_path}")
    print("   แล้วตรวจสอบว่ามีบรรทัด: FLIKOVER_LOGIN_URL, FLIKOVER_EMAIL, FLIKOVER_PASSWORD ครบหรือไม่")
    exit()

OCR_API_KEY = "helloworld"

# --- Export Config ---
ROOT_DIR = os.path.dirname(current_dir)
INPUT_RESEARCH_DIR = os.path.join(ROOT_DIR, "output", "research")
BASE_OUTPUT_DIR = os.path.join(ROOT_DIR, "data", "exports")
IGNORE_DOMAINS = [
    "pinterest.com", "pantip.com", "facebook.com", "shopee.co.th", "lazada.co.th", 
    "youtube.com", "instagram.com", "tiktok.com", "twitter.com", "nocnoc.com"
]

# ✅ URL Template (Target อยู่ท้ายสุด)
FLIKOVER_URL_TEMPLATE = "https://ahn.flikover.com/v2-site-explorer/organic-keywords?brandedMode=all&chartGranularity=daily&chartInterval=year2&compareDate=prevMonth&country=allByLocation&currentDate=today&dataMode=text&hiddenColumns=&intentsAttrs=&keywordRules=&limit=50&localMode=all&mainOnly=0&mode=subdomains&multipleUrlsOnly=0&offset=0&orgKeywordTraffic=1-&performanceChartTopPosition=top11_20%7C%7Ctop21_50%7C%7Ctop3%7C%7Ctop4_10%7C%7Ctop51&positionChanges=&sort=OrganicTrafficInitial&sortDirection=desc&urlRules=&volume_type=monthly&target={}"

# ================= 🛠️ HELPER FUNCTIONS =================
def solve_captcha_ocr_space(image_bytes: bytes) -> str:
    print("   📡 ส่งรูปไปแกะข้อความ...")
    try:
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        image_data = f"data:image/png;base64,{base64_image}"
        payload = {
            'apikey': OCR_API_KEY,
            'base64Image': image_data, 'language': 'eng', 
            'isOverlayRequired': False, 'scale': True, 'OCREngine': 2, 'detectOrientation': False
        }
        r = requests.post('https://api.ocr.space/parse/image', data=payload, timeout=5)
        if r.status_code != 200: return ""
        result = r.json()
        if result.get('IsErroredOnProcessing'): return ""
        parsed = result.get('ParsedResults')
        if parsed and isinstance(parsed, list):
            text_result = parsed[0].get('ParsedText', '')
            return ''.join(filter(str.isdigit, text_result))
        return ""
    except: return ""

def sanitize_filename(name):
    """Replace OS-illegal characters with dashes, preserving Thai (U+0E00-U+0E7F) and other Unicode."""
    name = re.sub(r'[^\w\s\-\u0E00-\u0E7F.]', '-', name)
    return name.strip().replace(' ', '_')


def filename_from_url(url):
    """Build a CSV filename from a URL."""
    # [FIX 1] Decode URL ก่อน เพื่อลดความยาว (เช่น %E0%B8... -> ภาษาไทย)
    url = unquote(url) 

    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.strip('/')
    if path:
        name = f"{domain}-{path.replace('/', '-')}"
    else:
        name = domain
    
    clean_name = sanitize_filename(name)

    # [FIX 2] ตัดความยาวชื่อไฟล์ไม่ให้เกิน 100 ตัวอักษร (แก้ปัญหา Save ไม่ได้)
    if len(clean_name) > 100:
        clean_name = clean_name[:100]

    return clean_name + ".csv"

def get_domain_from_url(url):
    try:
        parsed_uri = urlparse(url)
        domain = parsed_uri.netloc
        if domain.startswith("www."): domain = domain[4:]
        return domain.lower()
    except: return ""

def clean_traffic_number(value):
    try:
        if isinstance(value, (int, float)): return value
        value = str(value).strip().upper().replace(',', '')
        if value == '-' or value == '': return 0
        if 'K' in value: return float(value.replace('K', '')) * 1000
        if 'M' in value: return float(value.replace('M', '')) * 1000000
        return float(value)
    except: return 0


def detect_encoding(file_path):
    """Detect file encoding by reading BOM or trying common encodings."""
    with open(file_path, 'rb') as f:
        raw = f.read(4)

    if raw.startswith(b'\xff\xfe'): return 'utf-16-le'
    elif raw.startswith(b'\xfe\xff'): return 'utf-16-be'
    elif raw.startswith(b'\xff\xfe\x00\x00'): return 'utf-32-le'
    elif raw.startswith(b'\x00\x00\xfe\xff'): return 'utf-32-be'
    elif raw.startswith(b'\xef\xbb\xbf'): return 'utf-8-sig'
    else: return None


def read_csv_with_encoding(file_path):
    """Read CSV file with automatic encoding detection."""
    detected = detect_encoding(file_path)

    if detected:
        encodings_to_try = [detected]
        if detected.startswith('utf-16'):
            encodings_to_try.append('utf-16')
    else:
        encodings_to_try = []

    encodings_to_try.extend(['utf-16', 'utf-16-le', 'utf-8-sig', 'utf-8', 'cp1252', 'latin-1'])
    seen = set()
    encodings_to_try = [x for x in encodings_to_try if not (x in seen or seen.add(x))]

    last_error = None
    for encoding in encodings_to_try:
        try:
            if 'utf-16' in encoding.lower():
                df = pd.read_csv(file_path, encoding=encoding, sep='\t', on_bad_lines='skip')
            else:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, sep='\t', on_bad_lines='skip')
                    if df.shape[1] == 1:
                        df = pd.read_csv(file_path, encoding=encoding, on_bad_lines='skip')
                except:
                    df = pd.read_csv(file_path, encoding=encoding, on_bad_lines='skip')

            if df is not None and not df.empty:
                return df
        except Exception as e:
            last_error = e
            continue

    raise ValueError(f"Failed to read CSV with any encoding: {last_error}")

# ================= 📊 CSV PROCESSING FUNCTION =================
def merge_keyword_csv(keyword_dir, keyword_name):
    all_urls_dir = os.path.join(keyword_dir, "all_urls")
    output_path = os.path.join(keyword_dir, f"{keyword_name}.csv")

    print(f"\n   🧹 กำลังรวมไฟล์ CSV สำหรับ keyword: {keyword_name}")

    if not os.path.exists(all_urls_dir):
        print(f"      ⚠️ ไม่พบโฟลเดอร์: {all_urls_dir}")
        return

    csv_files = []
    for fname in os.listdir(all_urls_dir):
        fpath = os.path.join(all_urls_dir, fname)
        if fname.endswith('.csv') and os.path.isfile(fpath):
            csv_files.append(fpath)

    if not csv_files:
        print(f"      ⚠️ ไม่พบไฟล์ CSV สำหรับ keyword: {keyword_name}")
        return

    REQUIRED_COL_COUNT = 11

    dfs = []
    for file_path in csv_files:
        fname = os.path.basename(file_path)

        if os.path.getsize(file_path) == 0:
            print(f"      ⚠️ Skipping empty/invalid file: {fname}")
            continue

        df = None
        try:
            df = read_csv_with_encoding(file_path)
        except Exception as e:
            print(f"      ⚠️ Skipping empty/invalid file: {fname} ({e})")
            continue

        if df is None or df.empty:
            print(f"      ⚠️ Skipping empty/invalid file: {fname}")
            continue

        if df.shape[1] < REQUIRED_COL_COUNT:
            print(f"      ⚠️ Skipping empty/invalid file: {fname} (only {df.shape[1]} columns, need {REQUIRED_COL_COUNT})")
            continue

        df_subset = df.iloc[:, [0, 6, 10]].copy()
        df_subset.columns = ['Keyword', 'Volume', 'Organic traffic']
        dfs.append(df_subset)

    if not dfs:
        print(f"      ⚠️ ไม่มีข้อมูลสำหรับ keyword: {keyword_name}")
        return

    full_df = pd.concat(dfs, ignore_index=True)
    full_df['Sort_Value'] = full_df['Organic traffic'].apply(clean_traffic_number)
    full_df = full_df.sort_values(by='Sort_Value', ascending=False)
    full_df = full_df.drop_duplicates(subset=['Keyword'], keep='first')
    final_df = full_df[['Keyword', 'Volume', 'Organic traffic']]

    final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"   ✅ สร้างไฟล์รวมสำเร็จ: {output_path} ({len(final_df)} คีย์เวิร์ด)")

# ================= 🚀 MAIN PROGRAM =================
def run_automation():
    if not os.path.exists(INPUT_RESEARCH_DIR):
        print(f"Input directory not found: {INPUT_RESEARCH_DIR}")
        return

    keyword_targets = {}
    for keyword_folder in sorted(os.listdir(INPUT_RESEARCH_DIR)):
        folder_path = os.path.join(INPUT_RESEARCH_DIR, keyword_folder)
        if not os.path.isdir(folder_path):
            continue

        competitions_file = os.path.join(folder_path, f"{keyword_folder}-competitions.json")
        if not os.path.exists(competitions_file):
            continue

        print(f"Loading: {keyword_folder}-competitions.json")
        try:
            with open(competitions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # [FIX 3] เรียงลำดับตาม Rank (1, 2, 3...) ก่อนตัดเอา Top 3
            if isinstance(data, list):
                data.sort(key=lambda x: x.get('rank', 999))
                
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"   Skip invalid JSON: {e}")
            continue

        if not isinstance(data, list):
            continue

        count = 0
        for entry in data:
            if count >= 3:
                break
            
            # [FIX 4] Decode URL ตรงนี้เลย เพื่อแก้ปัญหา Double Encoding ตอนส่ง Request
            url = entry.get('url', '') if isinstance(entry, dict) else ''
            if not url:
                continue
            
            url = unquote(url) # แปลงเป็น URL ปกติที่ยังไม่ Encoded

            domain = get_domain_from_url(url)
            if any(blk in domain for blk in IGNORE_DOMAINS):
                continue
            
            if keyword_folder not in keyword_targets:
                keyword_targets[keyword_folder] = []
            keyword_targets[keyword_folder].append(url)
            count += 1

    all_targets = [(kw, url) for kw, urls in keyword_targets.items() for url in urls]

    if not all_targets:
        print("No usable URLs found in competitions JSON files")
        return

    print(f"\nTotal target URLs: {len(all_targets)} ({len(keyword_targets)} keywords)\n")

    with sync_playwright() as p:
        print("🚀 Launching Browser...")
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(viewport={"width": 1280, "height": 720}, accept_downloads=True)
        page = context.new_page()

        # PART 1: AUTO LOGIN
        MAX_RETRIES = 10
        login_success = False
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"\n⚡ Login รอบที่ {attempt}/{MAX_RETRIES}...")
            try:
                page.goto(LOGIN_URL, timeout=30000)
                page.locator("input[name*='mail']").fill(EMAIL)
                page.locator("input[type='password']").fill(PASSWORD)

                captcha_el = page.locator("#siimage")
                captcha_el.wait_for(state="visible", timeout=5000)
                time.sleep(1)
                img_bytes = captcha_el.screenshot()
                captcha_text = solve_captcha_ocr_space(img_bytes)
                if not captcha_text or len(captcha_text) < 4:
                    random_code = str(random.randint(100000, 999999))
                    captcha_text = random_code
                else:
                    print(f"   ✅ OCR อ่านได้: {captcha_text}")

                page.locator("input[placeholder='Security Code']").fill(captcha_text)
                page.locator("button:has-text('Sign in'), input[value='Sign in']").click()

                try:
                    page.wait_for_url(lambda u: u != LOGIN_URL, timeout=5000)
                    print("\n🎉🎉 LOGIN SUCCESS! 🎉🎉")
                    login_success = True
                    break
                except:
                    print("   ❌ Login ไม่ผ่าน (Captcha/Pass ผิด) -> ลองใหม่")
            except Exception as e:
                print(f"   💥 Error Login: {e}")
                continue

        if not login_success:
            browser.close()
            return

        # PART 2: DATA EXPORT
        print("\n⏳ กำลังเตรียม Export ข้อมูล...")
        time.sleep(2)

        total = len(all_targets)
        for i, (keyword, target_url) in enumerate(all_targets):
            
            # target_url ตรงนี้คือแบบ unquoted แล้ว (อ่านง่าย)
            csv_name = filename_from_url(target_url) 
            save_dir = os.path.join(BASE_OUTPUT_DIR, keyword, "all_urls")
            os.makedirs(save_dir, exist_ok=True)
            save_file_path = os.path.join(save_dir, csv_name)

            if os.path.exists(save_file_path):
                print(f"  [{i+1}/{total}] Skip (exists): {keyword}/all_urls/{csv_name}")
                continue

            # quote อีกครั้งเฉพาะตอนใส่ใน URL Template (ป้องกัน Double Encode)
            encoded_target = quote(target_url, safe='')
            full_ahrefs_url = FLIKOVER_URL_TEMPLATE.format(encoded_target)

            print(f"  [{i+1}/{total}] Opening: {csv_name} (keyword: {keyword})")
            try:
                page.goto(full_ahrefs_url, timeout=60000)
                time.sleep(8)
                try:
                    export_btn = page.locator("button:has-text('Export')").first
                    export_btn.wait_for(state="visible", timeout=15000)
                    export_btn.click()

                    modal = page.locator("div[role='dialog']")
                    modal.wait_for(state="visible", timeout=15000)

                    page.locator("text='CSV (UTF-16, best for Excel)'").click()
                    time.sleep(5)

                    modal_export_btn = modal.locator("button:has-text('Export')")
                    with page.expect_download(timeout=60000) as download_info:
                        modal_export_btn.click()

                    download = download_info.value
                    download.save_as(save_file_path)
                    print(f"    Saved: {keyword}/all_urls/{csv_name}")
                    time.sleep(3)
                except Exception as e:
                    print(f"    Export failed: {e}")
            except Exception as e:
                print(f"    Error loading page: {e}")

        browser.close()

    # PART 3: Merge CSVs
    for keyword in keyword_targets:
        keyword_dir = os.path.join(BASE_OUTPUT_DIR, keyword)
        merge_keyword_csv(keyword_dir, keyword)
    print("\n🎉 ทำงานครบทุกขั้นตอนแล้ว!")

if __name__ == "__main__":
    run_automation()