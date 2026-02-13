import os
import asyncio
import aiohttp
import argparse
import sys
import json
from pathlib import Path
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION (loaded from config.yaml)
# ==========================================
from config_loader import get_openrouter_config, get_model_config, load_prompt

_or_cfg = get_openrouter_config()
_model_cfg = get_model_config("first_sentence")

MODEL_NAME = _model_cfg["model"]
OPENROUTER_URL = _or_cfg["api_url"]
OPENROUTER_API_KEY = _or_cfg["api_key"]
HTTP_REFERER = _or_cfg["http_referer"]
FS_TEMPERATURE = _model_cfg.get("temperature", 0.3)
FS_X_TITLE = _model_cfg.get("x_title", "Privato First Sentence Gen")

SYSTEM_PROMPT = load_prompt("first_sentence_system.md")

class FirstSentenceGenerator:
    def __init__(self, args):
        self.base_dir = Path("output/research")
        self.concurrency = args.concurrency
        self.semaphore = asyncio.Semaphore(self.concurrency)

    async def call_gemini(self, html_content: str, keyword: str) -> str:
        """Sends full HTML to Gemini to generate the specific first sentence."""
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": HTTP_REFERER,
            "X-Title": FS_X_TITLE
        }

        # We instruct the model that the user message IS the context_html
        user_prompt = f"<context_html>\n{html_content}\n</context_html>"

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": FS_TEMPERATURE,
            "response_format": {"type": "json_object"}
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(OPENROUTER_URL, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = data['choices'][0]['message']['content'].strip()
                        return result
                    else:
                        error_text = await resp.text()
                        print(f"   [API Error] {keyword}: {error_text}")
                        return None
            except Exception as e:
                print(f"   [Request Error] {keyword}: {e}")
                return None

    def save_json_output(self, json_path: Path, new_sentence: str):
        """
        Handles the JSON file logic:
        - If not exists: create new.
        - If exists & valid: update 'first_sentence', keep others.
        - If exists & invalid: overwrite.
        """
        data = {}
        
        # Try to read existing file
        if json_path.exists():
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        data = json.loads(content)
            except json.JSONDecodeError:
                print(f"   [JSON Warning] {json_path.name} was invalid. Overwriting.")
                data = {} # Reset if invalid

        # Update key
        data['first_sentence'] = new_sentence

        # Write back
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def process_keyword(self, keyword: str):
        async with self.semaphore:
            # PATH RESOLUTION according to Spec
            # html_in: output/research/{keyword}/{keyword}.html
            # json_out: output/research/{keyword}/{keyword}-meta-seo.json
            
            html_path = self.base_dir / keyword / f"{keyword}.html"
            json_path = self.base_dir / keyword / f"{keyword}-meta-seo.json"

            # VALIDATION: Check HTML exists
            if not html_path.exists():
                print(f"[{keyword}] Skipped: HTML file not found.")
                return

            # LOAD CONTEXT
            try:
                with open(html_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Basic validation: Check if empty or no cues
                if not html_content or len(html_content) < 50:
                    print(f"[{keyword}] Skipped: HTML content too empty.")
                    return
                    
            except Exception as e:
                print(f"[{keyword}] Read Error: {e}")
                return

            print(f"[{keyword}] Analyzing HTML & Generating Sentence...")

            # GENERATE
            response_str = await self.call_gemini(html_content, keyword)

            if response_str:
                try:
                    # Clean markdown code blocks if present
                    clean_json = response_str.replace("```json", "").replace("```", "").strip()
                    response_obj = json.loads(clean_json)
                    
                    if "first_sentence" in response_obj:
                        sentence = response_obj["first_sentence"]
                        
                        # SAVE JSON
                        self.save_json_output(json_path, sentence)
                        print(f"[{keyword}] Success -> Saved to JSON.")
                    else:
                        print(f"[{keyword}] Error: API returned JSON but missing 'first_sentence' key.")
                except json.JSONDecodeError:
                    print(f"[{keyword}] Error: API did not return valid JSON. Response: {response_str[:50]}...")
            else:
                print(f"[{keyword}] Failed to generate response.")

    async def run(self, keywords_file: str):
        if not os.path.exists(keywords_file):
            print(f"Keywords file not found: {keywords_file}")
            return

        # Read, Trim, Dedup, Skip Empty
        unique_keywords = []
        seen = set()
        
        with open(keywords_file, 'r', encoding='utf-8') as f:
            for line in f:
                raw = line.strip()
                if raw and raw not in seen:
                    unique_keywords.append(raw)
                    seen.add(raw)

        print(f"Starting First Sentence Generation for {len(unique_keywords)} keywords.")
        print(f"Model: {MODEL_NAME}")
        
        tasks = [self.process_keyword(kw) for kw in unique_keywords]
        await asyncio.gather(*tasks)

# ==========================================
# MAIN ENTRY POINT
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="First Sentence Generator (JSON Output)")
    parser.add_argument("--keywords", default="data/keywords/keywords.txt", help="Path to keywords file")
    parser.add_argument("--concurrency", type=int, default=5, help="Concurrency limit")
    
    args = parser.parse_args()
    
    if "sk-or-v1" not in OPENROUTER_API_KEY:
         print("WARNING: Please check your OPENROUTER_API_KEY.")

    generator = FirstSentenceGenerator(args)
    
    # Run Async Loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(generator.run(args.keywords))