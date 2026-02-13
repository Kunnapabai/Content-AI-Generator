import requests
import json
import os
import time
from datetime import datetime
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

def main():
    # --- 1. Load Config ---
    print("⚙️  Phase Google Autocomplete (Task-based Advanced)")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_env_name = "User & Password.env"
    
    possible_env_paths = [
        os.path.join(current_dir, target_env_name),
        os.path.join(current_dir, "..", target_env_name),
        os.path.join(os.getcwd(), target_env_name)
    ]
    
    env_path = next((p for p in possible_env_paths if os.path.exists(p)), None)
    if env_path:
        load_dotenv(env_path)
        print(f"✅ Loaded Config: {target_env_name}")
    else:
        print(f"❌ Error: ไม่พบไฟล์ {target_env_name}")
        return

    LOGIN = os.getenv("DATAFORSEO_LOGIN")
    PASSWORD = os.getenv("DATAFORSEO_PASSWORD")
    CREDENTIALS = HTTPBasicAuth(LOGIN, PASSWORD)
    DEBUG = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")

    # --- 2. API Configuration (Autocomplete Endpoint) ---
    # ✅ ใช้ Autocomplete task-based + advanced mode (ต้องใช้ /advanced ไม่ใช่ /regular)
    URL_POST = "https://api.dataforseo.com/v3/serp/google/autocomplete/task_post"
    URL_GET = "https://api.dataforseo.com/v3/serp/google/autocomplete/task_get/advanced"
    URL_LIVE = "https://api.dataforseo.com/v3/serp/google/autocomplete/live/advanced"
    
    LOCATION_CODE = 2764
    LANGUAGE_CODE = "th"
    BASE_OUTPUT_DIR = "output/research"

    # --- Autocomplete Conditions ---
    # Condition 3: Word Prefix
    PREFIXES = ["แบบ", "ต่อเติม", "ขาย", "ติดตั้ง"]

    # Condition 4: Word Suffix
    SUFFIXES = [
        "คือ", "ราคา", "ข้อดี ข้อเสีย", "ขนาด", "แบบไหนดี", "สวยๆ",
        "ยี่ห้อไหนดี", "กับ", "vs", "ติดตั้ง", "สี", "เหล็ก", "หนา", "ดีไหม"
    ]

    # Condition 5: Alphabet Suffix (Thai Characters)
    THAI_CHARS = [
        "ห", "โ", "ก", "ข", "บ", "แ", "ร", "น",
        "ด", "ไ", "ย", "ส", "อ", "ล", "ว", "ค"
    ]

    # --- 3. Input Setup ---
    possible_input_paths = [
        r"data\keywords\keywords.txt",
        "data/keywords/keywords.txt",
        os.path.join(current_dir, "..", "data", "keywords", "keywords.txt")
    ]
    INPUT_FILE = next((p for p in possible_input_paths if os.path.exists(p)), None)

    if not INPUT_FILE:
        print("❌ Error: ไม่พบไฟล์ keywords.txt")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        seed_keywords = [line.strip() for line in f if line.strip()]

    print(f"📂 Loaded {len(seed_keywords)} seed keywords.")
    print("=" * 60)

    # --- 4. Process Loop ---
    for kw in seed_keywords:
        print(f"🎯 Keyword: [{kw}]")

        # Generate all query variations from the 5 conditions
        variations = generate_query_variations(kw, PREFIXES, SUFFIXES, THAI_CHARS)
        total_variations = len(variations)
        print(f"   📝 Generated {total_variations} query variations")

        all_suggestions = set()
        condition_results = {}

        for i, var in enumerate(variations):
            query = var["query"]
            condition = var["condition"]
            print(f"   [{i+1}/{total_variations}] Querying: '{query}' ({condition})")

            suggestions = fetch_autocomplete(
                query, CREDENTIALS, URL_LIVE, URL_POST, URL_GET,
                LOCATION_CODE, LANGUAGE_CODE, DEBUG
            )

            condition_results[condition] = {
                "query": query,
                "suggestions": suggestions,
                "count": len(suggestions)
            }

            all_suggestions.update(suggestions)

        all_suggestions = sorted(list(all_suggestions))

        if all_suggestions:
            print(f"   ✨ Total unique suggestions: {len(all_suggestions)}")
        else:
            print(f"   ❌ ไม่พบคำแนะนำจากทุก condition")

        # Save Logic
        keyword_folder = os.path.join(BASE_OUTPUT_DIR, kw)
        os.makedirs(keyword_folder, exist_ok=True)

        output_filename = f"{kw}-autocomplete.json"
        output_path = os.path.join(keyword_folder, output_filename)

        output_data = {
            "base_keyword": kw,
            "source": "google_autocomplete_advanced",
            "total_unique": len(all_suggestions),
            "total_queries": total_variations,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "suggestions": all_suggestions,
            "condition_results": condition_results
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)

        print(f"   💾 Saved to: {output_path}")
        print("-" * 60)


def generate_query_variations(seed_kw, prefixes, suffixes, thai_chars):
    """
    Generate autocomplete query variations based on 5 conditions:
    1. No Blank - seed keyword as-is
    2. With Blank - seed keyword + trailing space
    3. Word Prefix - specific words before seed keyword
    4. Word Suffix - specific words after seed keyword
    5. Alphabet Suffix - Thai characters after seed keyword
    """
    variations = []

    # Condition 1: No Blank (seed keyword as-is)
    variations.append({"query": seed_kw, "condition": "no_blank"})

    # Condition 2: With Blank (seed keyword + space)
    variations.append({"query": f"{seed_kw} ", "condition": "with_blank"})

    # Condition 3: Word Prefix
    for prefix in prefixes:
        variations.append({"query": f"{prefix} {seed_kw}", "condition": f"prefix_{prefix}"})

    # Condition 4: Word Suffix
    for suffix in suffixes:
        variations.append({"query": f"{seed_kw} {suffix}", "condition": f"suffix_{suffix}"})

    # Condition 5: Alphabet Suffix (Thai Characters)
    for char in thai_chars:
        variations.append({"query": f"{seed_kw} {char}", "condition": f"alphabet_{char}"})

    return variations


def extract_suggestions(task_data):
    """Deep-extract suggestion strings from any DataForSEO task response."""
    KEYS = ('suggestion', 'keyword', 'search_term', 'spell_check')
    suggestions = []

    results = task_data.get('result') or task_data.get('results') or []
    if isinstance(results, dict):
        results = [results]

    for res_obj in results:
        if not isinstance(res_obj, dict):
            continue
        for item in (res_obj.get('items') or []):
            if not isinstance(item, dict):
                continue
            for key in KEYS:
                val = item.get(key)
                if val and isinstance(val, str):
                    suggestions.append(val)

    return sorted(set(suggestions))


def fetch_autocomplete(keyword, credentials, url_live, url_post, url_get, loc, lang, debug=False):
    """Fetch autocomplete suggestions — live endpoint first, task-based fallback."""
    payload = [{
        "keyword": keyword,
        "location_code": loc,
        "language_code": lang
    }]

    # --- Strategy 1: Live Advanced ---
    max_live_retries = 5
    for attempt in range(max_live_retries):
        try:
            res = requests.post(url_live, json=payload, auth=credentials)
            data = res.json()

            top_status = data.get('status_code')
            tasks = data.get('tasks') or []
            task_item = tasks[0] if tasks else None
            task_status = task_item.get('status_code') if task_item else None

            # 40602 at task level = queued — retry
            if task_status == 40602:
                print(f"      ⏳ Task in queue (40602), retry {attempt+1}/{max_live_retries}...")
                time.sleep(2)
                continue

            # Top-level API error — no point retrying
            if top_status != 20000:
                msg = data.get('status_message', 'unknown')
                print(f"      ⚠️ Live API error (status {top_status}): {msg}")
                break

            if not task_item:
                print("      ⚠️ Live response missing task data")
                break

            # Task-level error — no point retrying
            if task_status != 20000:
                msg = task_item.get('status_message', 'unknown')
                print(f"      ⚠️ Live task error (status {task_status}): {msg}")
                break

            # Valid response — return results (even if empty)
            suggestions = extract_suggestions(task_item)
            if debug and not suggestions:
                print("      🔍 DEBUG [live]: 0 suggestions — raw response:")
                print(json.dumps(task_item, indent=2, ensure_ascii=False))
            return suggestions

        except Exception as e:
            print(f"      ⚠️ Live exception: {e}")
            break

    # --- Strategy 2: Task-based Advanced (async with polling) ---
    try:
        post_res = requests.post(url_post, json=payload, auth=credentials)
        post_data = post_res.json()

        if post_data.get('status_code') != 20000:
            print(f"      ❌ Task post failed: {post_data.get('status_message')}")
            return []

        task_id = post_data['tasks'][0]['id']

        max_retries = 30
        for i in range(max_retries):
            wait = 2 if i < 5 else 5
            time.sleep(wait)

            get_res = requests.get(f"{url_get}/{task_id}", auth=credentials)
            get_data = get_res.json()

            top_status = get_data.get('status_code')

            # Non-retriable API-level error — stop polling
            if top_status != 20000:
                msg = get_data.get('status_message', 'unknown')
                if top_status and top_status >= 50000:
                    # Server-side error — may resolve on retry
                    continue
                print(f"      ❌ Task get failed (status {top_status}): {msg}")
                return []

            task_item = get_data['tasks'][0]
            task_status = task_item.get('status_code')

            # Task still processing — keep polling
            if task_status in (20100, 40602):
                continue

            # Task completed — extract and return results
            if task_status in (20000, 20200):
                suggestions = extract_suggestions(task_item)
                if debug and not suggestions:
                    print("      🔍 DEBUG [task]: completed but 0 suggestions — raw response:")
                    print(json.dumps(task_item, indent=2, ensure_ascii=False))
                return suggestions

            # Unexpected task status — stop polling
            if debug:
                print(f"      🔍 DEBUG [task]: unexpected status {task_status} — raw response:")
                print(json.dumps(task_item, indent=2, ensure_ascii=False))
            print(f"      ⚠️ Task returned unexpected status: {task_status}")
            return []

        print(f"      ❌ Task timed out after {max_retries} retries")
        return []

    except Exception as e:
        print(f"      ❌ Task exception: {e}")
        return []

if __name__ == "__main__":
    main()