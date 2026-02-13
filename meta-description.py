import os
import asyncio
import aiohttp
import argparse
import json
import sys
from pathlib import Path
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION
# ==========================================
MODEL_NAME = "google/gemini-3-flash-preview"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"

# System Prompt: ถอดแบบจาก Prompt Engineering Panel ในไฟล์ HTML
SYSTEM_PROMPT = """
You are a Senior SEO Strategist and Content Marketer.
Analyze the provided article content and generate optimized metadata in JSON format.

## REQUIREMENTS:
1.  **meta_title**: Catchy, includes the main keyword, 50-60 characters max.
2.  **meta_description**: High CTR, summarizes value, includes keyword, under 160 characters.
3.  **slug**: URL-friendly, English translation of keyword if needed, lowercase, hyphens only.
4.  **tags**: Array of 5-8 relevant tags (comma-separated logic in JSON array).
5.  **excerpt**: A short summary (2-3 sentences) for blog preview cards.

## OUTPUT FORMAT:
Return ONLY valid JSON. No markdown formatting (no ```json ... ```).
Example:
{
  "meta_title": "...",
  "meta_description": "...",
  "slug": "...",
  "tags": ["...", "..."],
  "excerpt": "..."
}
"""

class MetaGenerator:
    def __init__(self, args):
        self.input_dir = Path("output/research")       # รับ HTML จาก Phase 6/7.1
        self.output_dir = Path("data/articles")        # ส่งออกไปที่ data/articles (ตามไฟล์ระบุ)
        self.concurrency = args.concurrency
        self.semaphore = asyncio.Semaphore(self.concurrency)

    async def call_gemini_json(self, article_text: str, keyword: str) -> dict:
        """เรียก Gemini และบังคับให้ตอบเป็น JSON"""
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://privatocontent.com",
            "X-Title": "Privato SEO Meta Gen"
        }
        
        user_prompt = f"""
        Main Keyword: "{keyword}"
        
        === ARTICLE CONTENT BEGIN ===
        {article_text[:15000]} 
        === ARTICLE CONTENT END ===
        
        Generate the SEO metadata JSON now.
        """
        # หมายเหตุ: Slice text ไว้ที่ 15000 chars เพื่อประหยัด token (Flash Lite รับได้เยอะ แต่ประหยัดไว้ก่อน)

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.5, # สมดุลระหว่างความคิดสร้างสรรค์และความถูกต้อง
            "response_format": { "type": "json_object" } # บังคับ JSON Mode
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(OPENROUTER_URL, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data['choices'][0]['message']['content']
                        try:
                            return json.loads(content)
                        except json.JSONDecodeError:
                            print(f"   [JSON Error] Raw content: {content[:50]}...")
                            return None
                    else:
                        print(f"   [API Error] {await resp.text()}")
                        return None
            except Exception as e:
                print(f"   [Request Error] {e}")
                return None

    async def process_keyword(self, keyword: str):
        async with self.semaphore:
            # Input: output/research/{keyword}/{keyword}.html
            input_path = self.input_dir / keyword / f"{keyword}.html"
            
            # Output: data/articles/{keyword}/metadata.json
            output_folder = self.output_dir / keyword
            output_path = output_folder / "metadata.json"
            
            if not input_path.exists():
                print(f"[{keyword}] Skipped: HTML file not found.")
                return

            # อ่าน HTML เพื่อดึง Text
            try:
                with open(input_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                soup = BeautifulSoup(html_content, 'html.parser')
                # เอาเฉพาะ Text ใน Article เพื่อไม่ให้ Token บวมด้วย HTML Tags
                article_text = soup.get_text(separator=' ', strip=True)
                
            except Exception as e:
                print(f"[{keyword}] Read Error: {e}")
                return

            print(f"[{keyword}] Generating Metadata (Gemini Flash Lite)...")

            # ส่ง AI
            metadata = await self.call_gemini_json(article_text, keyword)

            if metadata:
                # สร้าง Folder ปลายทางถ้ายังไม่มี
                output_folder.mkdir(parents=True, exist_ok=True)
                
                # บันทึก JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=4, ensure_ascii=False)
                
                print(f"[{keyword}] Success: JSON saved to {output_path}")
            else:
                print(f"[{keyword}] Failed to generate metadata.")

    async def run(self, keywords_file: str):
        if not os.path.exists(keywords_file):
            print(f"Keywords file not found: {keywords_file}")
            return

        with open(keywords_file, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        print(f"Starting Phase 7.2: Meta Description Generation for {len(keywords)} items.")
        
        tasks = [self.process_keyword(kw) for kw in keywords]
        await asyncio.gather(*tasks)

# ==========================================
# MAIN ENTRY POINT
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 7.2: SEO Meta Generation")
    parser.add_argument("--keywords", default="data/keywords/keywords.txt", help="Path to keywords file")
    parser.add_argument("--concurrency", type=int, default=5, help="Parallel processing limit")
    
    args = parser.parse_args()
    
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY environment variable not set.")
        sys.exit(1)

    # Check dependencies
    try:
        import bs4
    except ImportError:
        print("Error: beautifulsoup4 is required. Run 'pip install beautifulsoup4'")
        sys.exit(1)

    generator = MetaGenerator(args)
    asyncio.run(generator.run(args.keywords))