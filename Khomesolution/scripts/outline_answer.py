import os
import re
import asyncio
import aiohttp
import argparse
from pathlib import Path
from typing import Optional, List, Tuple

# ==========================================
# CONFIGURATION (loaded from config.yaml)
# ==========================================
from config_loader import get_openrouter_config, get_model_config, load_prompt

_or_cfg = get_openrouter_config()
_model_cfg = get_model_config("outline_answer")

MODEL_NAME = _model_cfg["model"]
OPENROUTER_URL = _or_cfg["api_url"]
OPENROUTER_API_KEY = _or_cfg["api_key"]
HTTP_REFERER = _or_cfg["http_referer"]
OA_TEMPERATURE = _model_cfg.get("temperature", 0.4)
OA_MAX_TOKENS = _model_cfg.get("max_tokens", 4096)
OA_X_TITLE = _model_cfg.get("x_title", "Privato Article Generator")

# System Prompt (loaded from PROMPTS/)
SYSTEM_PROMPT = load_prompt("outline_answer_system.md")

class ArticleGenerator:
    def __init__(self, args):
        self.outline_dir = Path("output/research") # แหล่งเก็บ Outline
        self.research_dir = Path("data/deep-research")
        self.output_dir = Path("output/research")
        self.concurrency = args.concurrency
        self.semaphore = asyncio.Semaphore(self.concurrency)

    def parse_outline_sections(self, outline_content: str) -> List[Tuple[str, str]]:
        """แยก Outline เป็น Section ตาม H2 แต่ละอัน (รวม H3 ที่อยู่ภายใน)"""
        sections = []
        current_section_lines = []
        current_h2 = None

        for line in outline_content.splitlines():
            stripped = line.strip()
            # ตรวจจับ <h1> แยกออก (ไม่นับเป็น section)
            if stripped.startswith("<h1>"):
                continue
            # ตรวจจับ comment lines
            if stripped.startswith("<!--") and stripped.endswith("-->"):
                continue
            # ตรวจจับ <h2> = เริ่ม section ใหม่
            if stripped.startswith("<h2>"):
                # บันทึก section ก่อนหน้า
                if current_h2 and current_section_lines:
                    sections.append(("\n".join(current_section_lines), current_h2))
                current_h2 = re.sub(r"</?h2>", "", stripped).strip()
                current_section_lines = [stripped]
            elif stripped.startswith("<h3>"):
                current_section_lines.append(stripped)
            elif stripped:
                current_section_lines.append(stripped)

        # บันทึก section สุดท้าย
        if current_h2 and current_section_lines:
            sections.append(("\n".join(current_section_lines), current_h2))

        return sections

    async def call_ai_writer(self, prompt: str) -> Optional[str]:
        """ส่งข้อมูลให้ AI เขียนบทความ"""
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": HTTP_REFERER,
            "X-Title": OA_X_TITLE
        }

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": OA_TEMPERATURE,
            "max_tokens": OA_MAX_TOKENS
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(OPENROUTER_URL, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data['choices'][0]['message']['content']
                        # ล้าง Code block formatting ถ้า AI เผลอใส่มา
                        content = content.replace("```markdown", "").replace("```html", "").replace("```", "").strip()
                        return content
                    else:
                        print(f"  API Error {resp.status}: {await resp.text()}")
                        return None
            except Exception as e:
                print(f"  Request Exception: {e}")
                return None

    def load_file(self, path: Path) -> Optional[str]:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        return None

    def markdown_to_html(self, md_content: str) -> str:
        """แปลง Markdown พื้นฐานเป็น HTML (ไม่ต้องพึ่ง library ภายนอก)"""
        lines = md_content.split('\n')
        html_lines = []
        in_ul = False
        in_ol = False

        for line in lines:
            stripped = line.strip()

            # ปิด list ถ้าบรรทัดไม่ใช่ list item
            if in_ul and not stripped.startswith('- ') and not stripped.startswith('* '):
                html_lines.append('</ul>')
                in_ul = False
            if in_ol and not re.match(r'^\d+\.\s', stripped):
                html_lines.append('</ol>')
                in_ol = False

            if not stripped:
                continue
            elif stripped.startswith('### '):
                html_lines.append(f'<h3>{stripped[4:]}</h3>')
            elif stripped.startswith('## '):
                html_lines.append(f'<h2>{stripped[3:]}</h2>')
            elif stripped.startswith('- ') or stripped.startswith('* '):
                if not in_ul:
                    html_lines.append('<ul>')
                    in_ul = True
                html_lines.append(f'<li>{stripped[2:]}</li>')
            elif re.match(r'^\d+\.\s', stripped):
                if not in_ol:
                    html_lines.append('<ol>')
                    in_ol = True
                text = re.sub(r'^\d+\.\s', '', stripped)
                html_lines.append(f'<li>{text}</li>')
            else:
                html_lines.append(f'<p>{stripped}</p>')

        if in_ul:
            html_lines.append('</ul>')
        if in_ol:
            html_lines.append('</ol>')

        html = '\n'.join(html_lines)
        # แปลง **bold**
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        return html

    async def process_keyword(self, keyword: str):
        """Flow หลัก: แยก Outline เป็น Section -> Gen ทีละ Section -> รวมไฟล์"""
        async with self.semaphore:
            # 1. กำหนด Path
            keyword_dir = self.output_dir / keyword
            prompt_dir = keyword_dir / "prompt"
            answer_dir = keyword_dir / "answer"
            outline_path = self.outline_dir / keyword / f"{keyword}-outline-optimized.md"
            research_path = self.research_dir / f"{keyword}-research-optimized.md"
            merged_md_path = keyword_dir / f"{keyword}.md"
            final_html_path = keyword_dir / f"{keyword}.html"

            # สร้างโฟลเดอร์
            prompt_dir.mkdir(parents=True, exist_ok=True)
            answer_dir.mkdir(parents=True, exist_ok=True)

            # 2. Skip ถ้ามี output สุดท้ายแล้ว
            if final_html_path.exists():
                print(f"[{keyword}] Skipped: Final HTML already exists.")
                return

            # 3. โหลดไฟล์ Input
            outline_content = self.load_file(outline_path)
            research_content = self.load_file(research_path)

            if not outline_content:
                print(f"[{keyword}] Error: Outline not found at {outline_path.resolve()}")
                return
            if not research_content:
                print(f"[{keyword}] Error: Research data not found at {research_path.resolve()}")
                return

            # 4. แยก Outline เป็น Sections
            sections = self.parse_outline_sections(outline_content)
            if not sections:
                print(f"[{keyword}] Error: No H2 sections found in outline.")
                return

            print(f"[{keyword}] Found {len(sections)} sections. Generating...")

            # 5. Gen ทีละ Section
            for idx, (section_outline, h2_title) in enumerate(sections, 1):
                section_num = f"{idx:02d}"
                prompt_path = prompt_dir / f"{section_num}-prompt.txt"
                answer_path = answer_dir / f"{section_num}-answer.md"

                # Skip ถ้า answer มีอยู่แล้ว (resume ได้)
                if answer_path.exists():
                    print(f"  [{keyword}] Section {section_num} skipped (answer exists).")
                    continue

                # สร้าง Prompt
                user_prompt = f"""KEYWORD: {keyword}

=== SECTION OUTLINE (Write ONLY this section) ===
{section_outline}
=== END SECTION OUTLINE ===

=== FULL RESEARCH DATA ===
{research_content}
=== END RESEARCH DATA ===

Please write the content for this section now in Markdown format.
"""
                # บันทึก Prompt
                with open(prompt_path, 'w', encoding='utf-8') as f:
                    f.write(user_prompt)

                # เรียก AI
                print(f"  [{keyword}] Section {section_num}: {h2_title}...")
                answer_content = await self.call_ai_writer(user_prompt)

                if answer_content:
                    with open(answer_path, 'w', encoding='utf-8') as f:
                        f.write(answer_content)
                    print(f"  [{keyword}] Section {section_num}: Done ({len(answer_content)} chars)")
                else:
                    print(f"  [{keyword}] Section {section_num}: FAILED")
                    return  # หยุดถ้า section ใด fail

            # 6. Merge answers -> .md
            print(f"[{keyword}] Merging answers...")
            merged_parts = []
            for idx in range(1, len(sections) + 1):
                answer_path = answer_dir / f"{idx:02d}-answer.md"
                content = self.load_file(answer_path)
                if content:
                    merged_parts.append(content)
                else:
                    print(f"  [{keyword}] Warning: Missing answer {idx:02d}")

            merged_md = "\n\n".join(merged_parts)
            with open(merged_md_path, 'w', encoding='utf-8') as f:
                f.write(merged_md)
            print(f"[{keyword}] Merged MD saved ({len(merged_md)} chars)")

            # 7. Convert to HTML -> .html
            html_body = self.markdown_to_html(merged_md)
            html_output = f"<article>\n{html_body}\n</article>"
            with open(final_html_path, 'w', encoding='utf-8') as f:
                f.write(html_output)
            print(f"[{keyword}] Final HTML saved ({len(html_output)} chars)")

    async def run(self, keywords_file: str):
        if not os.path.exists(keywords_file):
            print(f"Keywords file not found: {keywords_file}")
            return

        with open(keywords_file, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        print(f"Starting Phase 6: Section-by-Section Article Generation for {len(keywords)} keywords.")

        tasks = [self.process_keyword(kw) for kw in keywords]
        await asyncio.gather(*tasks)

# ==========================================
# MAIN ENTRY POINT
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Privato Content - Phase 6: Section-by-Section Article Generator")
    parser.add_argument("--keywords", default="data/keywords/keywords.txt", help="Path to keywords file")
    parser.add_argument("--concurrency", type=int, default=3, help="Parallel generation limit")

    args = parser.parse_args()

    if not OPENROUTER_API_KEY:
        print("Error: Please set OPENROUTER_API_KEY environment variable.")
    else:
        gen = ArticleGenerator(args)
        asyncio.run(gen.run(args.keywords))
