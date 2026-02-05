import re
import requests
import json
import os
import time
from urllib.parse import urlparse
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# ================= CONFIG =================
print("Phase 2: Google Competitor Analysis (DataForSEO Mode)")

# 1. Load Config (User & Password.env)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
env_path = os.path.join(root_dir, "User & Password.env")

if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv("User & Password.env")

LOGIN = os.getenv("DATAFORSEO_LOGIN")
PASSWORD = os.getenv("DATAFORSEO_PASSWORD")
CREDENTIALS = HTTPBasicAuth(LOGIN, PASSWORD)

if not LOGIN or not PASSWORD:
    print("Error: DataForSEO credentials not found in .env")
    exit()

# 2. Input Path
INPUT_KEYWORDS_FILE = os.path.join(root_dir, "data", "keywords", "keywords.txt")

# 3. Output Path -> output/research/{keyword}/
BASE_OUTPUT_DIR = os.path.join(root_dir, "output", "research")

# ================= FUNCTION =================
def get_dataforseo_serp(keyword):
    """Call DataForSEO Live Advanced to get full SERP data"""
    url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"

    payload = [{
        "keyword": keyword,
        "location_code": 2764,
        "language_code": "th",
        "device": "desktop",
        "os": "windows",
        "depth": 20
    }]

    try:
        response = requests.post(url, json=payload, auth=CREDENTIALS, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"   API Error: {response.status_code} {response.text}")
            return None
    except Exception as e:
        print(f"   Connection Error: {e}")
        return None


def extract_serp_items(api_response):
    """Safely extract the items array from the API response."""
    try:
        tasks = api_response.get("tasks")
        if not tasks:
            return None
        task = tasks[0]
        if task.get("status_code") != 20000:
            print(f"   Task error: {task.get('status_code')} {task.get('status_message')}")
            return None
        result = task.get("result")
        if not result:
            return None
        return result[0].get("items")
    except (IndexError, TypeError, KeyError) as e:
        print(f"   Parse error: {e}")
        return None


def extract_metadata(api_response):
    """Extract keyword, language_code, and location_code from task['data']."""
    try:
        tasks = api_response.get("tasks")
        if not tasks:
            return {}
        task = tasks[0]
        data = task.get("data", {})
        return {
            "keyword": data.get("keyword", ""),
            "language": data.get("language_code", ""),
            "country": data.get("location_code", 0),
        }
    except (IndexError, TypeError, KeyError):
        return {}


def domain_from_url(url):
    """Extract the domain from a URL, stripping the www. prefix."""
    try:
        host = urlparse(url).netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host
    except Exception:
        return ""


def parse_competitions(items):
    """Extract top 10 organic results with rank, domain, url, title, description."""
    competitors = []
    rank = 0
    for item in items:
        if item.get("type") == "organic":
            rank += 1
            url = item.get("url", "")
            competitors.append({
                "rank": rank,
                "domain": domain_from_url(url),
                "url": url,
                "title": item.get("title", ""),
                "description": item.get("description", ""),
            })
            if rank >= 10:
                break
    return competitors


def extract_paa_question(element):
    """Extract question text from a PAA element, trying multiple field names."""
    if isinstance(element, str):
        return element
    if isinstance(element, dict):
        # Try various field names used by DataForSEO
        return (
            element.get("title") or
            element.get("question") or
            element.get("text") or
            element.get("seed_question") or
            element.get("expanded_element", [{}])[0].get("title") if element.get("expanded_element") else None or
            ""
        )
    return ""


def extract_paa_from_item(item, collected):
    """Recursively extract PAA questions from an item and its nested structures."""
    if not isinstance(item, dict):
        return

    item_type = item.get("type", "")

    # Check if this item itself is a PAA question
    if item_type == "people_also_ask_element":
        question = extract_paa_question(item)
        if question and question not in collected:
            collected.append(question)

    # Check nested "items" array (common structure)
    nested_items = item.get("items", [])
    if isinstance(nested_items, list):
        for nested in nested_items:
            if isinstance(nested, dict):
                # Each nested item could be a PAA element
                question = extract_paa_question(nested)
                if question and question not in collected:
                    collected.append(question)
                # Recursively check for deeper nesting
                extract_paa_from_item(nested, collected)
            elif isinstance(nested, str) and nested and nested not in collected:
                collected.append(nested)

    # Check "expanded_element" array (alternative structure)
    expanded = item.get("expanded_element", [])
    if isinstance(expanded, list):
        for exp_item in expanded:
            question = extract_paa_question(exp_item)
            if question and question not in collected:
                collected.append(question)


def parse_keywords(items):
    """Extract people_also_ask questions and related_searches from ALL item types."""
    people_also_ask = []
    related_searches = []

    for item in items:
        item_type = item.get("type", "")

        # Handle People Also Ask block (multiple possible type names)
        if item_type in ("people_also_ask", "people_also_ask_element", "paa"):
            extract_paa_from_item(item, people_also_ask)

            # Also check direct question field on the block itself
            direct_question = extract_paa_question(item)
            if direct_question and direct_question not in people_also_ask:
                people_also_ask.append(direct_question)

        # Handle Related Searches block
        elif item_type == "related_searches":
            rs_items = item.get("items", [])
            for query in rs_items:
                # Related searches can be strings or objects with title/query field
                if isinstance(query, str) and query:
                    if query not in related_searches:
                        related_searches.append(query)
                elif isinstance(query, dict):
                    search_term = query.get("title") or query.get("query") or ""
                    if search_term and search_term not in related_searches:
                        related_searches.append(search_term)

    return {
        "people_also_ask": people_also_ask,
        "related_searches": related_searches,
    }


def sanitize_filename(name):
    """Replace OS-illegal characters with dashes, preserving Thai (U+0E00-U+0E7F) and other Unicode."""
    name = re.sub(r'[^\w\s\-\u0E00-\u0E7F.]', '-', name)
    return name.strip().replace(' ', '_')


# ================= MAIN PROCESS =================
def run():
    if not os.path.exists(INPUT_KEYWORDS_FILE):
        print(f"File not found: {INPUT_KEYWORDS_FILE}")
        return

    with open(INPUT_KEYWORDS_FILE, 'r', encoding='utf-8') as f:
        keywords = [line.strip() for line in f if line.strip()]

    print(f"Output Directory: {BASE_OUTPUT_DIR}")
    print(f"Loaded {len(keywords)} keywords")
    print("-" * 60)

    for index, kw in enumerate(keywords):
        print(f"[{index+1}/{len(keywords)}] Keyword: {kw}")

        safe_kw = sanitize_filename(kw)
        kw_dir = os.path.join(BASE_OUTPUT_DIR, safe_kw)
        os.makedirs(kw_dir, exist_ok=True)

        competitions_path = os.path.join(kw_dir, f"{safe_kw}-competitions.json")
        keywords_path = os.path.join(kw_dir, f"{safe_kw}-keywords.json")

        # Skip if both files already exist
        if os.path.exists(competitions_path) and os.path.exists(keywords_path):
            print("   Already exists (Skip)")
            continue

        data = get_dataforseo_serp(kw)
        if not data:
            print("   No response from DataForSEO")
            print("-" * 30)
            time.sleep(1)
            continue

        items = extract_serp_items(data)
        if not items:
            print("   No items in API response")
            print("-" * 30)
            time.sleep(1)
            continue

        # 1) Save competitions (organic results)
        if not os.path.exists(competitions_path):
            competitors = parse_competitions(items)
            if competitors:
                with open(competitions_path, 'w', encoding='utf-8') as f:
                    json.dump(competitors, f, ensure_ascii=False, indent=4)
                print(f"   Saved {len(competitors)} organic results -> {competitions_path}")
            else:
                print("   No organic results found")

        # 2) Save keywords (people_also_ask + related_searches) with metadata
        if not os.path.exists(keywords_path):
            kw_data = parse_keywords(items)
            metadata = extract_metadata(data)
            # Merge metadata with keyword data
            enriched_kw_data = {
                "keyword": metadata.get("keyword", kw),
                "language": metadata.get("language", ""),
                "country": metadata.get("country", 0),
                "people_also_ask": kw_data["people_also_ask"],
                "related_searches": kw_data["related_searches"],
            }
            if enriched_kw_data["people_also_ask"] or enriched_kw_data["related_searches"]:
                with open(keywords_path, 'w', encoding='utf-8') as f:
                    json.dump(enriched_kw_data, f, ensure_ascii=False, indent=4)
                print(f"   Saved {len(enriched_kw_data['people_also_ask'])} PAA + "
                      f"{len(enriched_kw_data['related_searches'])} related -> {keywords_path}")
            else:
                print("   No people_also_ask or related_searches found")

        print("-" * 30)
        time.sleep(1)

    print(f"\nDone! Files saved to {BASE_OUTPUT_DIR}")


if __name__ == "__main__":
    run()