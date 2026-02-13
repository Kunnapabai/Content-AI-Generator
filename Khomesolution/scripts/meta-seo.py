import os
import asyncio
import json
import argparse
import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, Any, Tuple

# ==========================================
# CONFIGURATION
# ==========================================
# ไฟล์ไม่ได้ระบุ Model จึงเปิดเป็น Config ไว้ (สามารถใส่ Logic Rule-based หรือ API ได้ที่นี่)
# ในที่นี้จะจำลองการทำงานของ Agent ตามหน้าที่ที่ระบุในไฟล์

class SEOWorkflow:
    def __init__(self, args):
        self.base_dir = Path(args.input_dir)
        self.concurrency = args.concurrency
        self.semaphore = asyncio.Semaphore(self.concurrency)

    # --- TASK 7.1: Agent 1 (Hook Specialist) ---
    async def run_agent_1_hook(self, text: str, keyword: str) -> str:
        """
        หน้าที่: Rewrite first sentence to be hooky.
        หมายเหตุ: ในการใช้งานจริง ส่วนนี้มักต้องใช้ LLM เพราะเป็นงาน Creative Writing
        แต่โค้ดนี้จะวางโครงสร้างไว้ให้ทำงานคู่ขนานได้
        """
        # จำลองการประมวลผล (Processing Simulation)
        await asyncio.sleep(1) # จำลองความหน่วง
        
        # TODO: ใส่ Code เรียก AI หรือ Logic การแก้ประโยคตรงนี้
        # ตัวอย่าง Logic เบื้องต้น: ดึงประโยคแรกออกมา (ยังไม่ได้ Rewrite จริง)
        sentences = text.split('.')
        first_sentence = sentences[0].strip() if sentences else ""
        
        # สมมติว่า Agent ทำงานเสร็จแล้วส่งค่ากลับมา
        print(f"   [Agent 1] Analyzed hook for: {keyword}")
        return first_sentence # คืนค่าประโยคแรก (หรือประโยคที่แก้แล้ว)

    # --- TASK 7.2: Agent 2 (SEO Strategist) ---
    async def run_agent_2_meta(self, text: str, keyword: str) -> Dict[str, str]:
        """
        หน้าที่: Generate Meta Data (Title, Desc, Slug, Excerpt) เป็น JSON
        """
        # จำลองการประมวลผล (Processing Simulation)
        await asyncio.sleep(1.5) # จำลองความหน่วง (อาจนานกว่า Agent 1)
        
        # ตัวอย่าง Logic แบบ Rule-based (ถ้าไม่ใช้ AI)
        # 1. Slug: แปลง Keyword เป็น slug
        slug = keyword.lower().replace(" ", "-")
        
        # 2. Meta Title: ใช้ประโยคแรกๆ หรือ Keyword
        meta_title = f"{keyword}: Complete Guide & Review"
        
        # 3. Meta Description: ตัดเอา 160 ตัวอักษรแรก
        meta_description = text[:157] + "..." if len(text) > 160 else text
        
        # 4. Excerpt: ตัดเอา 2 ประโยคแรก
        sentences = text.split('.')
        excerpt = '.'.join(sentences[:2]) + '.' if len(sentences) > 2 else text

        print(f"   [Agent 2] Generated Meta JSON for: {keyword}")
        
        return {
            "meta_title": meta_title,
            "meta_description": meta_description,
            "slug": slug,
            "excerpt": excerpt
        }

    # --- MAIN ORCHESTRATOR (Parallel Execution) ---
    async def process_keyword(self, keyword: str):
        async with self.semaphore:
            html_file = self.base_dir / keyword / f"{keyword}.html"
            json_output = self.base_dir / keyword / f"{keyword}-seo.json"
            
            if not html_file.exists():
                print(f"[{keyword}] Skipped: HTML not found.")
                return

            # 1. อ่านไฟล์ HTML (Input)
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            soup = BeautifulSoup(html_content, 'html.parser')
            article_text = soup.get_text(strip=True)
            
            # หาประโยคแรกเพื่อส่งให้ Agent 1 (หรือส่งทั้งบทความ)
            first_p = soup.find('p')
            first_p_text = first_p.get_text() if first_p else ""

            print(f"[{keyword}] Starting Parallel Agents...")

            # ======================================================
            # PARALLEL EXECUTION (หัวใจสำคัญของ Phase 7)
            # สั่งงาน Agent 1 และ Agent 2 พร้อมกันด้วย asyncio.gather
            # ======================================================
            task_7_1 = self.run_agent_1_hook(first_p_text, keyword)
            task_7_2 = self.run_agent_2_meta(article_text, keyword)

            # รอให้ทั้งคู่เสร็จ (Parallel Wait)
            results = await asyncio.gather(task_7_1, task_7_2)
            
            # Unpack ผลลัพธ์
            new_hook_sentence = results[0] # ผลจาก Agent 1
            meta_data = results[1]         # ผลจาก Agent 2

            # ======================================================
            # MERGE & SAVE (Orchestrator รวบรวมผล)
            # ======================================================
            
            # 1. อัปเดต HTML ด้วย Hook ใหม่ (จาก Agent 1)
            if first_p and new_hook_sentence:
                # Logic การแทนที่ประโยคเดิม (ง่ายๆ คือแทนที่ P แรก)
                # หมายเหตุ: ถ้าใช้ Logic จริงต้องระวังไม่ให้ทับทั้ง Paragraph
                # อันนี้จำลองว่า Agent 1 ส่งมาแค่ประโยคแรก เราก็แปะกลับไป
                current_text = first_p.string or ""
                # สมมติ Logic การ Merge ง่ายๆ
                first_p.string = new_hook_sentence + current_text[len(new_hook_sentence):] 

            # 2. บันทึกไฟล์ HTML (ทับไฟล์เดิม)
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))

            # 3. บันทึกไฟล์ JSON (จาก Agent 2)
            with open(json_output, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, indent=4, ensure_ascii=False)

            print(f"[{keyword}] Success: Agents synchronized & outputs saved.")

    async def run(self, keywords_file: str):
        if not os.path.exists(keywords_file):
            print("Keywords file not found.")
            return

        with open(keywords_file, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        print(f"Starting Phase 7: Parallel SEO Agents for {len(keywords)} items.")
        
        tasks = [self.process_keyword(kw) for kw in keywords]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Privato Phase 7: Parallel SEO Workflow")
    parser.add_argument("--keywords", default="data/keywords/keywords.txt")
    parser.add_argument("--input-dir", default="output/research")
    parser.add_argument("--concurrency", type=int, default=5)
    
    args = parser.parse_args()
    
    workflow = SEOWorkflow(args)
    asyncio.run(workflow.run(args.keywords))