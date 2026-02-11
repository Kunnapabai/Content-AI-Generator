import os
import json
import asyncio
import argparse
import aiohttp
import time
from typing import List, Dict, Optional
from pathlib import Path

# ==========================================
# CONFIGURATION & CONSTANTS
# ==========================================
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "x-ai/grok-4"
DEFAULT_TIMEOUT = 90
MAX_RETRIES = 3

SYSTEM_PROMPT = """
## SYSTEM ROLE
You are a **Home Improvement & Building Materials research strategist**. For every optimized outline you receive, convert the hierarchy (H1 → H2 → H3/H4) into **3–7 ordered research phases**. Each phase must stitch together related headings so earlier phases provide the prerequisite context for later ones. Your deliverables become instructions for human researchers.

### Source Context
We are a home solution center specializing in quality building materials including roofing (ShinkoLite, Shingle, UPVC), doors & windows (TOSTEM, UPVC, aluminum), bathroom fixtures (Trump Glass, American Standard), safety screens, and home improvement products with professional installation services.

---

## INPUT PAYLOAD (PER INVOCATION)
You receive a single user prompt with:
- `KEYWORD` – literal keyword string.
- `OUTLINE_PATH` – absolute/relative path to `{keyword}-outline-optimized.md`.
- `OUTLINE_TEXT` – full outline contents (HTML headings only). If an inline outline is supplied between `<PAGE OUTLINE START>` / `<PAGE OUTLINE END>`, treat it as canonical and ignore the referenced file.
- Optional `INLINE_OUTLINE` – present only when caller overrides the file. When absent, rely on the file contents.

Abort immediately when the outline text is missing or empty.

---

## EXECUTION GUARDRAILS
1. **Keyword scope**: Process a single keyword at a time. If the runner provides a short keyword list, dedupe before iterating.
2. **Phase budget**: Minimum 3 phases, maximum 7. Merge redundant sections while keeping every SERP-critical idea represented.
3. **Hierarchy mapping**: Preserve the intent of each H2 block; H3/H4s become bulleted subtopics underneath the same phase section.
4. **Cross-link flow**: Sequence phases from fundamentals → materials/types → specifications/standards → selection criteria → installation/maintenance → buyer enablement. Later phases may reference earlier foundations but never repeat coverage verbatim.

---

## TECHNICAL VS INDUSTRY CLASSIFICATION
Classify every heading as **Technical/Standards** (construction standards, material durability, safety certifications, building codes, engineering specs, JIS/GB standards, performance testing) or **Industry/Trade** (manufacturer documentation, product specifications, trade publications, installer certifications, project case studies, pricing, warranties). Mixed sections inherit the strictest requirements from both lists.

### Geographic Scope
- Technical/Standards: limit to Japan, China, United States, Australia.
- Industry/Trade: limit to Japan (TOSTEM/LIXIL focus), China, Singapore.
- **Pricing Exception**: For pricing/availability data only, Thailand sources are permitted.
- Mixed phases must satisfy both sets simultaneously.
- **Japan Priority**: For doors, windows, and aluminum products, prioritize Japanese standards (JIS) and TOSTEM/LIXIL documentation.
- **China Priority**: For manufacturing specs, material sourcing, and cost-competitive alternatives, prioritize Chinese industry sources.

### Time Frames
- Technical/Standards sources: past 24 months; building codes and JIS/GB standards remain valid longer—flag only if superseded.
- Industry/Trade: past 12 months for pricing/availability; product specs valid unless discontinued.
- Fundamentals/background: prioritize 2020–2025 for material science and installation best practices.

### Source Quality
- Technical: JIS (Japanese Industrial Standards), GB (Chinese National Standards), ASTM testing reports, ISO construction specs, material engineering journals, energy efficiency studies, AS/NZS (Australian/New Zealand Standards).
- Industry: Brand documentation (TOSTEM, LIXIL, American Standard, ShinkoLite), Japanese/Chinese trade publications, distributor catalogs, official product spec sheets, installation manuals, warranty documents, certified installer guidelines.
- **Pricing Only**: Thai distributor pricing (HomePro, SCG, Builk) permitted for pricing/availability comparisons.

### Language & Audience
English output only; written for homeowners and business-savvy professionals; define technical jargon (e.g., U-value, thermal break, UPVC) briefly when first introduced.

### Output Format (per finding)
- Bullet form, 2–5 concise phrases (≤40 words) containing concrete metrics or specs (e.g., thickness, U-value, warranty years, price range).
- Label each recommendation with an evidence level: **Strong** (JIS/GB certified, official brand specs, lab-tested), **Moderate** (trade publication, installer consensus, regional distributor data), **Preliminary** (user reviews, recent product launch, limited field data).

---

## SEARCH GUIDANCE
Build multilingual Boolean queries for every phase:
- Technical: English + Japanese + Chinese variants joined with `OR`, add domain filters such as `site:jisc.go.jp`, `site:astm.org`, `site:buildingscience.com`, `site:gb688.cn`, `site:standards.org.au`.
- Industry: English + Japanese + Chinese; include vendor domains (e.g., `site:lixil.com`, `site:lixil.co.jp`, `site:tostem.lixil.co.jp`, `site:alibaba.com`, `site:made-in-china.com`).
- **Pricing Only**: For pricing queries, add Thai domains: `site:homepro.co.th`, `site:scgbuildingmaterials.com`, `site:builk.com`.
- Example patterns:
  - Doors/Windows: `"TOSTEM door specifications" OR "TOSTEM ドア 仕様" OR "LIXIL aluminum door specs"`.
  - Roofing: `"UPVC roofing durability" OR "polycarbonate roofing specifications" OR "ポリカーボネート屋根"`.
  - Bathroom: `"American Standard specifications" OR "bathroom fixtures installation guide" OR "LIXIL bathroom Japan"`.

---

## REQUIRED OUTPUT STRUCTURE
For each phase `N` emit exactly this scaffold (repeat sequentially):

Phase N:
Please conduct comprehensive research on [concise description of grouped headings]. Your research should cover:

[H2 title from outline]:
- map each H3/H4 bullet as subtopics (short phrases)

[Next H2 title as needed]:
- additional subtopics

Research Requirements:
- Geographic Scope: [Technical vs Industry rules applied to this phase]
- Time Frame: [explicit recency windows per classification]
- Source Quality: [references to allowable source types]
- Output Format: Bullet points, 2–5 phrases each ≤40 words with concrete specs/metrics
- Language: English only
- Audience: Homeowners and professionals seeking building material guidance
- Search Queries: [phase-specific multilingual Boolean guidance]
- Evidence Levels: Tag every recommendation as Strong / Moderate / Preliminary based on support strength

General rules:
- Preserve the original heading language/tone; do not invent new H2 topics, only rewrite for clarity when merging.
- Ensure successive phases build context; later phases may reference prior outputs but cannot restate bullets verbatim.
- Keep instructions readable plain text (no Markdown fences around the entire response). Blank line between major blocks is acceptable.

---

## FAILURE HANDLING
- If the outline file/inline text is missing or empty, respond with `Missing outline: <resolved_path>` and stop.
- If headings cannot be parsed (no `<h1>`/`<h2>` present), output `Data unavailable — required SERP data missing.`
- Never emit partial phases after a failure message.
"""

# ==========================================
# HELPER CLASSES & FUNCTIONS
# ==========================================

class ResearchPipeline:
    def __init__(self, args):
        self.chunk_size = args.chunk_size
        self.max_concurrency = args.max_concurrency
        self.timeout = args.timeout
        self.incremental = args.incremental
        self.base_output_dir = Path("output")
        self.checkpoint_file = Path("checkpoints/deepresearch_checkpoint.json")
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        
        # Ensure directories exist
        self.base_output_dir.mkdir(exist_ok=True)
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)

    def load_keywords(self, filepath: str) -> List[str]:
        """Load keywords from text file."""
        path = Path(filepath)
        if not path.exists():
            print(f"Error: Keywords file not found at {filepath}")
            return []
        with open(path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]

    def load_checkpoint(self) -> List[str]:
        """Load list of completed keywords."""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("completed", [])
            except json.JSONDecodeError:
                return []
        return []

    def save_checkpoint(self, completed_keywords: List[str]):
        """Save progress to JSON."""
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump({"completed": completed_keywords, "timestamp": time.time()}, f, indent=2)

    async def call_openrouter(self, messages: List[Dict]) -> Optional[str]:
        """Call OpenRouter API with retry logic."""
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://privatocontent.com", # Required by OpenRouter rules
            "X-Title": "Privato Content Pipeline"
        }
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": 0.2, # Low temp for structured output
            "max_tokens": 8000
        }

        for attempt in range(MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        OPENROUTER_URL, 
                        json=payload, 
                        headers=headers, 
                        timeout=self.timeout
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return data['choices'][0]['message']['content']
                        elif response.status == 429:
                            # Rate limit handling
                            wait_time = 2 ** attempt
                            print(f"Rate limited. Retrying in {wait_time}s...")
                            await asyncio.sleep(wait_time)
                        else:
                            print(f"API Error {response.status}: {await response.text()}")
                            return None
            except Exception as e:
                print(f"Request failed (Attempt {attempt+1}/{MAX_RETRIES}): {str(e)}")
                await asyncio.sleep(1)
        
        return None

    async def process_keyword(self, keyword: str) -> bool:
        """Process a single keyword: Load Outline -> Generate Prompt -> Save."""
        async with self.semaphore:
            keyword_dir = self.base_output_dir / "research" / keyword
            input_file = keyword_dir / f"{keyword}-outline-optimized.md"
            output_file = keyword_dir / f"{keyword}-research-prompt.md"

            # 1. Validate Input
            if not input_file.exists():
                print(f"[{keyword}] Skipped: Outline file not found.")
                return False

            # 2. Check Incremental Skip
            if self.incremental and output_file.exists():
                print(f"[{keyword}] Skipped: Output already exists.")
                return True

            print(f"[{keyword}] Processing...")

            # 3. Read Outline
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    outline_content = f.read()
            except Exception as e:
                print(f"[{keyword}] Error reading outline: {e}")
                return False

            # 4. Construct Prompt
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"KEYWORD: {keyword}\n\nOUTLINE_TEXT:\n{outline_content}"}
            ]

            # 5. Call AI
            response_content = await self.call_openrouter(messages)
            
            if not response_content:
                print(f"[{keyword}] Failed: No response from API.")
                return False

            # 6. Save Output
            try:
                keyword_dir.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(response_content)
                print(f"[{keyword}] Success: Research prompt generated.")
                return True
            except Exception as e:
                print(f"[{keyword}] Error saving output: {e}")
                return False

    async def run(self, keywords_file: str):
        # Initial Setup
        if not OPENROUTER_API_KEY:
            print("Error: OPENROUTER_API_KEY environment variable is not set.")
            return

        all_keywords = self.load_keywords(keywords_file)
        completed_keywords = self.load_checkpoint()
        
        # Filter if incremental, though process_keyword also checks file existence
        # This helps strictly with the checkpoint list
        if self.incremental:
            keywords_to_process = [k for k in all_keywords if k not in completed_keywords]
        else:
            keywords_to_process = all_keywords

        total = len(keywords_to_process)
        print(f"Starting Phase 4: Deep Research Generation for {total} keywords.")
        print(f"Config: Concurrency={self.max_concurrency}, Chunk={self.chunk_size}, Model={MODEL_NAME}")

        # Chunk Processing
        for i in range(0, total, self.chunk_size):
            chunk = keywords_to_process[i : i + self.chunk_size]
            print(f"\n--- Processing Chunk {i//self.chunk_size + 1} ({len(chunk)} items) ---")
            
            tasks = [self.process_keyword(kw) for kw in chunk]
            results = await asyncio.gather(*tasks)
            
            # Update Checkpoint per chunk
            for kw, success in zip(chunk, results):
                if success and kw not in completed_keywords:
                    completed_keywords.append(kw)
            
            self.save_checkpoint(completed_keywords)
            print(f"Checkpoint saved. Progress: {len(completed_keywords)}/{len(all_keywords)}")

# ==========================================
# MAIN ENTRY POINT
# ==========================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Privato Content - Phase 4: Deep Research Prompt Gen")
    
    # CLI Flags matching the HTML parameters
    parser.add_argument("--keywords", default="data/keywords/keywords.txt", help="Path to keywords file")
    parser.add_argument("--chunk-size", type=int, default=200, help="Keywords per checkpoint")
    parser.add_argument("--max-concurrency", type=int, default=8, help="Parallel API requests")
    parser.add_argument("--timeout", type=int, default=90, help="HTTP timeout per request (seconds)")
    parser.add_argument("--incremental", action="store_true", help="Skip keywords with existing outputs")

    args = parser.parse_args()

    pipeline = ResearchPipeline(args)
    asyncio.run(pipeline.run(args.keywords))