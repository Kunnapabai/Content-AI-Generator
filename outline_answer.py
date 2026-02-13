import os
import asyncio
import aiohttp
import argparse
import json
from pathlib import Path
from typing import Optional, Dict

# ==========================================
# CONFIGURATION
# ==========================================
MODEL_NAME = "google/gemini-3-flash-preview"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"

# System Prompt: ถอดแบบมาจาก Objectives ใน HTML (Citation Injection, Tone Alignment)
SYSTEM_PROMPT = """
You are a Senior Technical Writer for the Privato Content system.
Your task is to write a comprehensive, professional article in HTML format based on the provided [OUTLINE] and [RESEARCH DATA].

## OBJECTIVES
1. **Follow the Outline:** Strictly adhere to the H2/H3 structure provided in the outline.
2. **Integrate Research:** Use the facts, statistics, and definitions from the provided research data.
3. **Citation Injection:** You MUST cite your sources. When using specific facts from the research, append the citation key (e.g., [1], [Source]) exactly as it appears in the research data.
4. **Tone Alignment:** Maintain a professional, authoritative, yet accessible tone (Technical/Educational).
5. **HTML Formatting:** Output ONLY valid HTML code inside <article> tags. Use proper headers (<h2>, <h3>), paragraphs (<p>), lists (<ul>, <ol>), and emphasize key terms (<strong>).

## RESTRICTIONS
- Do NOT output Markdown. Output HTML only.
- Do NOT include <html>, <head>, or <body> tags. Start directly with <article>.
- Do NOT invent information not present in the research data (No Hallucinations).
- Do NOT write an introduction or conclusion outside the <article> tags.
"""

class ArticleGenerator:
    def __init__(self, args):
        self.outline_dir = Path("output") # แหล่งเก็บ Outline
        self.research_dir = Path("data/deep-research")
        self.output_dir = Path("output/research")
        self.concurrency = args.concurrency
        self.semaphore = asyncio.Semaphore(self.concurrency)
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def call_ai_writer(self, prompt: str) -> Optional[str]:
        """ส่งข้อมูลให้ AI เขียนบทความ"""
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://privatocontent.com",
            "X-Title": "Privato Article Generator"
        }
        
        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4, # ต่ำเพื่อให้เกาะติดข้อมูลจริง
            "max_tokens": 4096 # รองรับบทความยาว
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(OPENROUTER_URL, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data['choices'][0]['message']['content']
                        # ล้าง Code block formatting ถ้า AI เผลอใส่มา
                        content = content.replace("```html", "").replace("```", "").strip()
                        return content
                    else:
                        print(f"API Error {resp.status}: {await resp.text()}")
                        return None
            except Exception as e:
                print(f"Request Exception: {e}")
                return None

    def load_file(self, path: Path) -> Optional[str]:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    async def process_keyword(self, keyword: str):
        """Flow การทำงานหลัก: อ่าน Outline + Research -> เขียนบทความ"""
        async with self.semaphore:
            # 1. กำหนด Path
            # Input 1: Outline (output/{keyword}/{keyword}-outline-optimized.md)
            outline_path = self.outline_dir / keyword / f"{keyword}-outline-optimized.md"
            
            # Input 2: Research (data/deep-research/{keyword}.optimized.md)
            research_path = self.research_dir / f"{keyword}.optimized.md"
            
            # Output: HTML File
            output_path = self.output_dir / keyword / f"{keyword}.html"
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 2. Validation
            if output_path.exists():
                print(f"[{keyword}] Skipped: Output already exists.")
                return

            outline_content = self.load_file(outline_path)
            research_content = self.load_file(research_path)

            if not outline_content:
                print(f"[{keyword}] Error: Outline not found.")
                return
            if not research_content:
                print(f"[{keyword}] Error: Research data not found.")
                return

            print(f"[{keyword}] Generating article (using {MODEL_NAME})...")

            # 3. Construct Prompt
            user_prompt = f"""
KEYWORD: {keyword}

=== START OUTLINE ===
{outline_content}
=== END OUTLINE ===

=== START RESEARCH DATA ===
{research_content}
=== END RESEARCH DATA ===

Please write the HTML article now.
"""

            # 4. Call AI
            html_content = await self.call_ai_writer(user_prompt)

            if html_content:
                # 5. Save Output
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"[{keyword}] Success: Article generated ({len(html_content)} chars).")
            else:
                print(f"[{keyword}] Failed: AI did not return content.")

    async def run(self, keywords_file: str):
        if not os.path.exists(keywords_file):
            print(f"Keywords file not found: {keywords_file}")
            return
            
        with open(keywords_file, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        print(f"Starting Phase 6: AI Article Generation for {len(keywords)} items.")
        
        tasks = [self.process_keyword(kw) for kw in keywords]
        await asyncio.gather(*tasks)

# ==========================================
# MAIN ENTRY POINT
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Privato Content - Phase 6: Article Generator")
    parser.add_argument("--keywords", default="data/keywords/keywords.txt", help="Path to keywords file")
    parser.add_argument("--concurrency", type=int, default=3, help="Parallel generation limit")
    
    args = parser.parse_args()
    
    if not OPENROUTER_API_KEY:
        print("Error: Please set OPENROUTER_API_KEY environment variable.")
    else:
        asyncio.run(generator.run(args.keywords))
        # หมายเหตุ: บรรทัดข้างบนควรเป็น asyncio.run(ArticleGenerator(args).run(args.keywords))
        # แก้ไขให้ถูกต้องด้านล่าง:
        gen = ArticleGenerator(args)
        asyncio.run(gen.run(args.keywords))