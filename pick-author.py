import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION
# ==========================================
AI_MODEL_NAME = "x-ai/grok-4"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = (
    "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"
)

# WordPress Configuration
WP_API_URL = os.getenv("WP_API_URL")  # e.g., "https://your-site.com/wp-json/wp/v2"
WP_USERNAME = os.getenv("WP_USERNAME")
WP_APP_PASSWORD = os.getenv(
    "WP_APP_PASSWORD"
)  # Application Password, NOT login password

# System Prompt สำหรับเลือกผู้เขียน
AUTHOR_SELECT_PROMPT = """
You are an Editor-in-Chief. analyze the provided article summary and the list of available authors.
Select the MOST SUITABLE author based on:
1. Topic Expertise (Does the author specialize in this field?)
2. Writing Tone (Does the author's style match the article?)

Output JSON ONLY:
{
  "selected_author_id": 123,
  "rationale": "Reason for selection..."
}
"""


class WordPressPublisher:
    def __init__(self, args):
        self.input_html_dir = Path("output/research")
        self.input_meta_dir = Path("data/articles")
        self.authors_file = Path("data/authors.json")
        self.concurrency = args.concurrency
        self.semaphore = asyncio.Semaphore(self.concurrency)

    def load_authors(self) -> List[Dict]:
        """โหลดข้อมูลผู้เขียนจากไฟล์ JSON"""
        if not self.authors_file.exists():
            print(f"Error: {self.authors_file} not found.")
            return []
        with open(self.authors_file, "r", encoding="utf-8") as f:
            return json.load(f)

    async def select_author_with_grok(
        self, article_text: str, authors: List[Dict]
    ) -> Optional[int]:
        """ใช้ Grok-2 เลือกผู้เขียนที่เหมาะสม"""
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://privatocontent.com",
            "X-Title": "Privato Author Picker",
        }

        # ตัดเนื้อหาบางส่วนเพื่อประหยัด Token
        summary = article_text[:2000]

        # แปลง List ผู้เขียนเป็น String ย่อๆ
        authors_str = json.dumps(
            [
                {
                    "id": a.get("wp_id"),
                    "name": a.get("name"),
                    "expertise": a.get("expertise"),
                    "tone": a.get("tone"),
                }
                for a in authors
            ],
            indent=2,
        )

        user_content = f"""
        AUTHORS LIST:
        {authors_str}

        ARTICLE CONTENT (Snippet):
        {summary}

        Select the best author ID.
        """

        payload = {
            "model": AI_MODEL_NAME,
            "messages": [
                {"role": "system", "content": AUTHOR_SELECT_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    OPENROUTER_URL, json=payload, headers=headers
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = json.loads(data["choices"][0]["message"]["content"])
                        return result.get("selected_author_id")
                    else:
                        print(f"   [AI Error] {await resp.text()}")
                        return None
            except Exception as e:
                print(f"   [AI Exception] {e}")
                return None

    async def post_to_wordpress(
        self, html_content: str, metadata: Dict, author_id: int
    ) -> bool:
        """ส่งข้อมูลไปยัง WordPress API"""
        if not WP_API_URL or not WP_USERNAME or not WP_APP_PASSWORD:
            print("   [WP Error] Missing WordPress credentials.")
            return False

        # Basic Auth for WordPress Application Password
        credentials = f"{WP_USERNAME}:{WP_APP_PASSWORD}"
        token = base64.b64encode(credentials.encode()).decode()
        headers = {
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        }

        # เตรียม Payload (Mapping ข้อมูลจาก Phase ก่อนหน้า)
        post_data = {
            "title": metadata.get("meta_title", "Untitled"),
            "content": html_content,
            "status": "draft",  # บังคับเป็น Draft ตาม Workflow
            "slug": metadata.get("slug"),
            "author": author_id,
            "excerpt": metadata.get("excerpt", ""),
            # การใส่ Tags อาจต้องแยก call หรือใช้ ID ขึ้นอยู่กับ WP config
            # "tags": metadata.get("tags", [])
        }

        async with aiohttp.ClientSession() as session:
            try:
                url = f"{WP_API_URL}/posts"
                async with session.post(url, json=post_data, headers=headers) as resp:
                    if resp.status == 201:  # 201 Created
                        data = await resp.json()
                        print(
                            f"   [WP Success] Post ID: {data['id']} | Link: {data['link']}"
                        )
                        return True
                    else:
                        print(f"   [WP Error] {resp.status}: {await resp.text()}")
                        return False
            except Exception as e:
                print(f"   [WP Exception] {e}")
                return False

    async def process_keyword(self, keyword: str, authors: List[Dict]):
        async with self.semaphore:
            # 1. เช็คไฟล์ Input
            html_path = self.input_html_dir / keyword / f"{keyword}.html"
            meta_path = self.input_meta_dir / keyword / "metadata.json"

            if not html_path.exists() or not meta_path.exists():
                print(f"[{keyword}] Skipped: Missing HTML or Metadata.")
                return

            print(f"[{keyword}] Processing Phase 9...")

            # 2. อ่านข้อมูล
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # ใช้ BeautifulSoup ดึง Text มาวิเคราะห์เพื่อเลือก Author
            soup = BeautifulSoup(html_content, "html.parser")
            text_for_analysis = soup.get_text(separator=" ", strip=True)

            # 3. เลือก Author (AI Grok)
            # ถ้าไม่มี authors ให้ใช้ default (เช่น ID 1)
            author_id = 1
            if authors:
                print(f"   Asking Grok to pick author...")
                suggested_id = await self.select_author_with_grok(
                    text_for_analysis, authors
                )
                if suggested_id:
                    author_id = suggested_id
                    print(f"   Selected Author ID: {author_id}")

            # 4. Post to WordPress
            success = await self.post_to_wordpress(html_content, metadata, author_id)

            if success:
                print(f"[{keyword}] Pipeline Complete.")
            else:
                print(f"[{keyword}] Failed to post.")

    async def run(self, keywords_file: str):
        if not os.path.exists(keywords_file):
            print("Keywords file not found.")
            return

        authors = self.load_authors()
        if not authors:
            print("Warning: No authors loaded. Will fallback to default Author ID 1.")

        with open(keywords_file, "r", encoding="utf-8") as f:
            keywords = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]

        print(f"Starting Phase 9: Publishing {len(keywords)} articles to WordPress.")

        tasks = [self.process_keyword(kw, authors) for kw in keywords]
        await asyncio.gather(*tasks)


# ==========================================
# MAIN ENTRY POINT
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 9: WP Publisher")
    parser.add_argument("--keywords", default="data/keywords/keywords.txt")
    parser.add_argument("--concurrency", type=int, default=3)

    args = parser.parse_args()

    # Check Env Vars
    if not all([OPENROUTER_API_KEY, WP_API_URL, WP_USERNAME, WP_APP_PASSWORD]):
        print(
            "Error: Missing Environment Variables (OPENROUTER_API_KEY, WP_API_URL, WP_USERNAME, WP_APP_PASSWORD)"
        )
        print("Please export them before running.")
    else:
        publisher = WordPressPublisher(args)
        asyncio.run(publisher.run(args.keywords))
