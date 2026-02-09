import os
import asyncio
import aiohttp
import argparse
import sys
import json
from pathlib import Path
from bs4 import BeautifulSoup

# ==========================================
# CONFIGURATION
# ==========================================
MODEL_NAME = "google/gemini-3-flash-preview"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = "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"

SYSTEM_PROMPT = """
# First Sentence Generator Specification

You are an expert Semantic SEO and Algorithmic Authorship methodology. You will be given the full HTML of a single article as: `<context_html>` Your job is to generate exactly ONE succinct, definitive first sentence that will appear immediately **below the main `<h1>`** of that article. This sentence must follow the Generation Rules defined below and must be strictly grounded in the information available inside `<context_html>`. Do NOT generate or discuss code, tools, or scripts. Your only output should be a single strict JSON object with one key: `"first_sentence"`.

---

## GENERATION RULES - FIRST SENTENCE BELOW `<h1>`

### 1. SCOPE

- Generate exactly ONE sentence.
- This sentence is intended to appear directly **under the main `<h1>`** of the article.
- It must:
  - Capture the macro context of the entire page.
  - Be strictly grounded in `<context_html>`.
  - Be ready to function as a snippet-worthy intro line.

### 2. UNDERSTAND THE PAGE FROM `<context_html>`

**From `<context_html>`, infer:**
- `<title>` text.
- The main `<h1>` text.
- Early paragraphs and visible copy.
- Any precise numeric facts that are clearly relevant to the topic.

**From this, decide:**
- **CENTRAL ENTITY:** the main "thing" (e.g., Germany, drinking water, contracts, email marketing).
- **CENTRAL SEARCH INTENT:** the main verb + entity combination that describes what users want here (e.g., "drinking water", "know/go Germany", "manage contracts", "send bulk email campaigns").
- **MACRO CONTEXT:** what the whole article is fundamentally about (e.g., "health benefits of drinking water", "how to apply for a German student visa", "what is contract management software").

The first sentence must reflect this macro context.

### 3. CLASSIFY THE H1 TYPE

Look at the main `<h1>` and classify the article's macro intent:

- **Definitional:**
  - "What is X?", "What is [topic]?", "X explained"
- **Boolean:**
  - "Can/Should/Is/Does X ...?"
- **How-to / procedural:**
  - "How to...", "How do you...", "Guide to...", "Step-by-step..."
- **List / grouping:**
  - "X benefits of...", "Top 10...", "Best tools for...", "Types of...", "Symptoms of..."
- **Comparative / superlative:**
  - "best", "worst", "most", "least", "cheapest", "safest", etc.
- **Other/brand:**
  - Branded or descriptive H1 ("Drinking Water: Health Benefits and Risks", "Contract Management Software Overview").

This classification determines the sentence pattern.

### 4. DECIDE THE CORE DECLARATION

Before writing, decide the single most important **declaration** that the sentence must contain:

- **If definitional:**
  - Provide a precise definition of the main entity in this article's context.
- **If how-to:**
  - State what doing X fundamentally involves or achieves.
- **If list:**
  - State that there are X key items and what kind they are.
- **If boolean:**
  - Give a clear Yes/No/Sometimes stance with the main condition.
- **If comparative:**
  - State which option(s) is best/most/least and why in one clause.
- **If other:**
  - Summarize the main promise or value of the article in one clear claim.

This declaration must appear in the **first clause** of the sentence. Do NOT delay it.

### 5. SENTENCE PATTERNS FOR THE H1 FIRST SENTENCE

Choose exactly ONE of these templates, adapted to the content of `<context_html>`:

#### 5.1. Definitional H1

**Pattern:**
- "[Main entity/phrase] is [short, precise definition tied to the page's core purpose]."

**Example:**
- **H1:** "What is contract management?"
- **Sentence:** "Contract management is the end-to-end process of creating, negotiating, storing, tracking, and renewing agreements so a business can reduce risk and capture more value."

#### 5.2. How-to / Guide H1

**Pattern:**
- "To [verb phrase from the H1], [main action or outcome grounded in the article's focus]."

**Example:**
- **H1:** "How to apply for a German student visa"
- **Sentence:** "To apply for a German student visa, you must choose the right visa type, gather the required documents, and submit your application on time to the correct consulate."

#### 5.3. List / Grouping H1

**Pattern:**
- "There are [number or 'several'] key [items] of [entity + attribute], and this guide explains [what they do / why they matter] so [target user] can [primary outcome]."

**Example:**
- **H1:** "20 health benefits of drinking water"
- **Sentence:** "There are many health benefits of drinking water, and this guide explains how proper hydration supports your energy, brain function, digestion, and long-term disease prevention."

(If the exact count is clearly given in the HTML, prefer a precise number: "20 health benefits..." -> "20 key health benefits...".)

#### 5.4. Boolean / Risk H1

**Pattern:**
- "Yes/No/Sometimes, [entity + main claim], if/when [key condition], and this article explains [how/why/outcomes]."

**Example:**
- **H1:** "Can you drink too much water?"
- **Sentence:** "Yes, you can drink too much water if you consistently overhydrate and dilute your blood sodium levels, and this article explains the symptoms, risks, and safe intake ranges."

#### 5.5. Comparative / Superlative H1

**Pattern:**
- "The [best/most/least etc.] [entity/option] for [target user or scenario] is/are those that [main criterion], and this guide shows you how to compare and choose them."

**Example:**
- **H1:** "Best marketing automation tools for small businesses"
- **Sentence:** "The best marketing automation tools for small businesses are platforms that unify email, CRM, and analytics in one place, and this guide shows you how to compare and choose them."

#### 5.6. Other / Brand / Descriptive H1

**Pattern:**
- "[Main entity/phrase] [is/helps/lets] [target user] [achieve primary outcome], and this article explains [how it works / why it matters] with clear, practical examples."

**Example:**
- **H1:** "Contract management software overview"
- **Sentence:** "Contract management software helps legal and operations teams centralize agreements, reduce manual work, and control renewal risk, and this overview explains how it works in practice."

### 6. MICRO-SEMANTICS & QUALITY RULES

For the single sentence you output:

#### 6.1. No fluff, no meta-talk

- Do NOT use phrases like:
  - "In this article, we will..."
  - "This blog post is about..."
- Go straight to the claim.

#### 6.2. No delayed answer

- The key declaration must appear before any long clause, "if", "when", "although", or side note.

#### 6.3. Control modality

- Prefer strong factual verbs when the HTML clearly supports them:
  - "increases", "reduces", "helps", "means", "is".
- If the H1 or article clearly indicates uncertainty or research nuance, you may use:
  - "can", "may", "might", "tends to" -- but keep them grounded in the text.

#### 6.4. Reuse H1 vocabulary

- Reuse the main nouns and attributes from the H1 in similar order, or tight synonyms clearly supported by `<context_html>`.
- Keep **entity + attribute** close together (good word proximity).

#### 6.5. Reflect macro context clearly

- The sentence must reflect:
  - The central entity (e.g., drinking water, Germany visa, marketing automation).
  - The central search intent (learn, apply, compare, understand, manage, send, etc.).
- It should feel like a single-sentence summary of the entire article's promise.

#### 6.6. Use numbers when grounded in HTML

- If `<context_html>` clearly states exact counts or numeric facts (e.g., "20 benefits", "60-70% of the body", "3 main steps"), use them.

#### 6.7. Length and density

- Aim for ~15-30 words.
- Must be exactly **one sentence** and self-contained.
- It should be usable as a featured snippet or top-of-article summary.

#### 6.8. Grounding

- Do NOT invent facts, research, brands, or numbers that are not clearly implied or stated in `<context_html>`.
- You may compress and paraphrase, but everything must be traceable to the HTML content (title, headings, body, data).

### 7. VALIDATION

Before finalizing, check:

- Is it ONE sentence only?
- Does it directly express what the article is about?
- Does it reuse key words from the H1 or its clear synonyms?
- Is it specific, not generic?
- Is it free from outlines/previews like "we will cover X, Y, and Z"?
- Is it consistent with the information actually present in `<context_html>`?

If any answer is "no", revise once. If it's still non-compliant, skip and record the issue.

---

## OUTPUT FORMAT (MANDATORY)

Your final output MUST be a single JSON object, and nothing else:

- Strict JSON
- Exactly one top-level key: "first_sentence"
- Value is the single generated sentence as a string.

Example (format only):
{
  "first_sentence": "Drinking water is the daily habit that keeps your body's physical, mental, and metabolic systems working properly, and this guide explains how to get enough every day."
}

Do NOT include comments, extra keys, explanations, or surrounding text. Return ONLY this JSON object.
"""

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
            "HTTP-Referer": "https://privatocontent.com",
            "X-Title": "Privato First Sentence Gen"
        }
        
        # We instruct the model that the user message IS the context_html
        user_prompt = f"<context_html>\n{html_content}\n</context_html>"

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3, # Low temperature for factual adherence
            "response_format": {"type": "json_object"} # Force JSON mode if supported
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