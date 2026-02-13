import os
import json
import asyncio
import argparse
import aiohttp
import time
from typing import List, Dict, Optional
from pathlib import Path

# ==========================================
# CONFIGURATION & CONSTANTS (loaded from config.yaml)
# ==========================================
from config_loader import get_openrouter_config, get_model_config, load_prompt

_or_cfg = get_openrouter_config()
_model_cfg = get_model_config("deepresearch_prompt")

OPENROUTER_API_KEY = _or_cfg["api_key"]
OPENROUTER_URL = _or_cfg["api_url"]
HTTP_REFERER = _or_cfg["http_referer"]
MODEL_NAME = _model_cfg["model"]
DEFAULT_TIMEOUT = _model_cfg.get("timeout", 90)
MAX_RETRIES = _model_cfg.get("max_retries", 3)
DR_TEMPERATURE = _model_cfg.get("temperature", 0.2)
DR_MAX_TOKENS = _model_cfg.get("max_tokens", 8000)
DR_MAX_CONCURRENCY = _model_cfg.get("max_concurrency", 8)
DR_X_TITLE = _model_cfg.get("x_title", "Privato Content Pipeline")

SYSTEM_PROMPT = load_prompt("deepresearch_prompt_system.md")

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
            "HTTP-Referer": HTTP_REFERER,
            "X-Title": DR_X_TITLE
        }
        payload = {
            "model": MODEL_NAME,
            "messages": messages,
            "temperature": DR_TEMPERATURE,
            "max_tokens": DR_MAX_TOKENS
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
    parser.add_argument("--max-concurrency", type=int, default=DR_MAX_CONCURRENCY, help="Parallel API requests")
    parser.add_argument("--timeout", type=int, default=90, help="HTTP timeout per request (seconds)")
    parser.add_argument("--incremental", action="store_true", help="Skip keywords with existing outputs")

    args = parser.parse_args()

    pipeline = ResearchPipeline(args)
    asyncio.run(pipeline.run(args.keywords))