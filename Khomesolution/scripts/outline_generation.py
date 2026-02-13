import asyncio
import aiohttp
import yaml
import json
import re
import argparse
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple

from config_loader import get_openrouter_config, get_model_config, load_prompt

# --- Configuration & Constants (loaded from config.yaml) ---
_or_cfg = get_openrouter_config()
_gen_cfg = get_model_config("outline_generation")
_ana_cfg = get_model_config("outline_analysis")

OPENROUTER_API_URL = _or_cfg["api_url"]
API_KEY = _or_cfg["api_key"]
HTTP_REFERER = _or_cfg["http_referer"]

# Default Parameters (from config.yaml)
DEFAULT_MAX_CONCURRENCY = _gen_cfg.get("max_concurrency", 10)
DEFAULT_CHUNK_SIZE = _gen_cfg.get("chunk_size", 500)
DEFAULT_TIMEOUT = _gen_cfg.get("timeout", 90)
DEFAULT_MODEL = _gen_cfg["model"]
DEFAULT_TEMPERATURE = _gen_cfg.get("temperature", 0.3)
DEFAULT_MAX_TOKENS = _gen_cfg.get("max_tokens", 4000)
GEN_X_TITLE = _gen_cfg.get("x_title", "Privato Outline Generator")
ANA_X_TITLE = _ana_cfg.get("x_title", "Privato Outline Analyzer")

# Paths
OUTPUT_DIR = Path("output/research")
CHECKPOINT_DIR = OUTPUT_DIR / "checkpoints"
CHECKPOINT_FILE = "outline_master_checkpoint.json"
LOG_DIR = Path("logs")
LOG_FILE = "outline_generation.log"
KEYWORDS_FILE = "data/keywords/keywords.txt"

# Rate Limiting
RATE_LIMIT_RPM = _gen_cfg.get("rate_limit_rpm", 60)

# Cost Estimation (per 1K tokens - Gemini Flash pricing)
COST_PER_1K_INPUT = 0.000075
COST_PER_1K_OUTPUT = 0.0003
EST_INPUT_TOKENS = 2500
EST_OUTPUT_TOKENS = 1200

# Source Context (hardcoded per HTML spec)
SOURCE_CONTEXT = "Home solution center specializing in roofing, doors, windows, bathroom fixtures with installation services."

# --- Prompts (loaded from PROMPTS/) ---
SYSTEM_PROMPT = load_prompt("outline_generation_system.md")
USER_PROMPT_TEMPLATE = load_prompt("outline_generation_user.md")
ANALYSIS_SYSTEM_PROMPT = load_prompt("outline_analysis_system.md")
ANALYSIS_USER_PROMPT_TEMPLATE = load_prompt("outline_analysis_user.md")


def setup_logging() -> logging.Logger:
    """Setup JSON-lines logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / LOG_FILE

    logger = logging.getLogger("outline_generation")
    logger.handlers = []
    logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(file_handler)

    return logger


def log_json(logger: logging.Logger, event: str, data: Dict[str, Any]):
    """Log event as JSON line."""
    entry = {"timestamp": datetime.now().isoformat(), "event": event, **data}
    logger.info(json.dumps(entry, ensure_ascii=False))


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, rpm: int = RATE_LIMIT_RPM):
        self.interval = 60.0 / rpm
        self.last_call = 0.0
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.time()
            wait = self.last_call + self.interval - now
            if wait > 0:
                await asyncio.sleep(wait)
            self.last_call = time.time()


class OutlineGenerator:
    """Koray-aligned SEO Outline Generator using OpenRouter API."""

    def __init__(self, args):
        self.args = args
        self.verbose = getattr(args, 'verbose', False)
        self.semaphore = asyncio.Semaphore(args.max_concurrency)
        self.timeout = aiohttp.ClientTimeout(total=args.timeout)
        self.rate_limiter = RateLimiter(RATE_LIMIT_RPM)
        self.logger = setup_logging()

        # Paths
        self.output_dir = OUTPUT_DIR
        self.checkpoint_path = CHECKPOINT_DIR / CHECKPOINT_FILE

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

        if self.verbose:
            print(f"[INIT] Output directory: {self.output_dir.absolute()}")
            print(f"[INIT] Checkpoint path: {self.checkpoint_path.absolute()}")

        # Stats
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "tokens_used": 0,
            "validation_warnings": 0,
            "structural_failures": 0,
            "analysis_success": 0,
            "analysis_failed": 0
        }

        # Load checkpoint
        self.checkpoint = self._load_checkpoint()

    def _load_checkpoint(self) -> Dict[str, Any]:
        """Load checkpoint file."""
        if self.checkpoint_path.exists():
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"completed": [], "failed": [], "last_index": 0}

    def _save_checkpoint(self):
        """Save checkpoint file."""
        self.checkpoint["updated_at"] = datetime.now().isoformat()
        with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(self.checkpoint, f, ensure_ascii=False, indent=2)

    def _load_serp_analysis(self, keyword: str) -> Optional[Dict]:
        """Load SERP analysis YAML for keyword."""
        serp_file = self.output_dir / keyword / f"{keyword}-serp-analysis.yaml"
        if self.verbose:
            print(f"  [SERP] Looking for: {serp_file}")

        if serp_file.exists():
            try:
                with open(serp_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if self.verbose:
                        print(f"  [SERP] Loaded successfully ({len(str(data))} chars)")
                    return data
            except Exception as e:
                print(f"  [ERROR] Failed to load SERP file: {e}")
                return None
        else:
            if self.verbose:
                print(f"  [SERP] File not found: {serp_file}")
        return None

    def _load_master_queries(self, keyword: str, limit: int = 50) -> str:
        """Load master queries CSV (first N rows)."""
        csv_file = self.output_dir / keyword / f"{keyword}-master-queries.csv"
        if csv_file.exists():
            with open(csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:limit + 1]
                return '\n'.join(lines)
        return "No query data available."

    def _detect_language(self, serp_data: Dict) -> str:
        """Detect language from SERP analysis."""
        meta = serp_data.get("meta", {})
        lang_detected = meta.get("language_detected", {})

        if isinstance(lang_detected, dict):
            iso = lang_detected.get("iso", "th")
            return "Thai" if iso == "th" else "English"

        lang = meta.get("language", "Thai")
        return lang

    def _extract_prompt_variables(self, serp_data: Dict) -> Dict[str, str]:
        """Extract key variables from SERP data for prompt injection."""
        # Top entities by salience
        entities = serp_data.get("entity_signals", [])
        if isinstance(entities, list):
            top_entities = [e.get("entity", e.get("name", "")) for e in sorted(
                entities, key=lambda x: x.get("salience", 0), reverse=True
            )[:5]]
        else:
            top_entities = []

        # Intent
        intent = serp_data.get("intent", {})
        primary_intent = intent.get("primary", "informational")
        micro_intents = intent.get("micro_intents", [])

        # Patterns
        patterns = serp_data.get("pattern_signals", {})
        dominant_patterns = patterns.get("dominant_patterns", [])

        # Title signals
        title_signals = serp_data.get("title_generation_signals", {})

        # Knowledge graph
        kg = serp_data.get("knowledge_graph", {})
        kg_edges = len(kg.get("edges", []))

        # Opportunities
        opportunities = serp_data.get("opportunity_gaps", [])
        opportunity_gaps = [o.get("gap", "") for o in opportunities[:3]] if opportunities else []

        return {
            "top_entities": ", ".join(top_entities) if top_entities else "N/A",
            "primary_intent": primary_intent,
            "micro_intents": ", ".join(micro_intents) if micro_intents else "N/A",
            "dominant_patterns": str(dominant_patterns)[:300] if dominant_patterns else "N/A",
            "title_signals": str(title_signals.get("angle_recommendations", []))[:200],
            "kg_edges": str(kg_edges),
            "opportunity_gaps": ", ".join(opportunity_gaps) if opportunity_gaps else "N/A"
        }

    def _format_serp_yaml(self, serp_data: Dict) -> str:
        """Format relevant SERP sections for prompt."""
        relevant = {}

        for key in ["meta", "intent", "entity_signals", "pattern_signals",
                    "title_generation_signals", "opportunity_gaps", "consensus_signals"]:
            if key in serp_data:
                relevant[key] = serp_data[key]

        # Trim entity_signals to top 5
        if "entity_signals" in relevant and isinstance(relevant["entity_signals"], list):
            relevant["entity_signals"] = sorted(
                relevant["entity_signals"],
                key=lambda x: x.get("salience", 0),
                reverse=True
            )[:5]

        return yaml.dump(relevant, allow_unicode=True, default_flow_style=False)

    def _validate_outline(self, content: str) -> Tuple[bool, List[str], bool]:
        """Validate outline against Koray framework.

        Returns:
            (is_valid, issues, is_structural_failure)
            - is_valid: True if no issues at all.
            - issues: list of human-readable issue strings.
            - is_structural_failure: True if total headings outside 25-30
              (hard reject — outline must NOT be saved).
        """
        issues = []
        is_structural_failure = False

        # Count headings
        h1_count = len(re.findall(r'<h1[^>]*>', content, re.IGNORECASE))
        h2_count = len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE))
        h3_count = len(re.findall(r'<h3[^>]*>', content, re.IGNORECASE))
        h4_count = len(re.findall(r'<h4[^>]*>', content, re.IGNORECASE))
        total_headings = h1_count + h2_count + h3_count + h4_count

        # Total headline count check — strict structural failure
        if total_headings < 25 or total_headings > 30:
            issues.append(
                f"STRUCTURAL FAILURE: total headings {total_headings} "
                f"(H1={h1_count} H2={h2_count} H3={h3_count} H4={h4_count}, "
                f"required 25-30)"
            )
            is_structural_failure = True

        # Single H1 check
        if h1_count != 1:
            issues.append(f"H1 count: {h1_count} (expected 1)")

        # Minimum H2 check
        if h2_count < 5:
            issues.append(f"H2 count: {h2_count} (minimum 5)")

        # Contextual Bridge check
        if "Contextual Bridge" not in content:
            issues.append("Missing <!-- Contextual Bridge --> marker")

        # Antonym Context check
        if "Antonym Context" not in content:
            issues.append("Missing <!-- Antonym Context --> marker")

        # Check for duplicates
        headings = re.findall(r'<h[1-4][^>]*>([^<]+)</h[1-4]>', content, re.IGNORECASE)
        unique = set(h.strip().lower() for h in headings)
        if len(unique) != len(headings):
            issues.append("Duplicate headings detected")

        # Check for non-HTML content
        non_html = sum(1 for line in content.split('\n')
                      if line.strip() and not line.strip().startswith('<')
                      and not line.strip().startswith('<!--'))
        if non_html > 2:
            issues.append(f"Contains {non_html} non-HTML lines")

        return len(issues) == 0, issues, is_structural_failure

    def _clean_outline(self, content: str) -> str:
        """Clean LLM output to pure HTML headings."""
        content = content.strip()

        # Remove code fences
        if content.startswith("```"):
            content = re.sub(r'^```\w*\n?', '', content)
            content = re.sub(r'\n?```$', '', content)

        # Keep only HTML lines and comments
        lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            if not stripped:
                lines.append('')
            elif stripped.startswith('<') or stripped.startswith('<!--'):
                lines.append(line)

        return '\n'.join(lines).strip()

    async def _analyze_outline(self, session: aiohttp.ClientSession,
                                keyword: str, keyword_index: int,
                                outline: str, retries: int = 3) -> Optional[Dict]:
        """Call OpenRouter API with outline analysis prompt."""
        user_prompt = ANALYSIS_USER_PROMPT_TEMPLATE.format(
            keyword=keyword,
            raw_outline=outline
        )

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": HTTP_REFERER,
            "X-Title": ANA_X_TITLE
        }

        payload = {
            "model": self.args.model,
            "messages": [
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.args.temperature,
            "max_tokens": self.args.max_tokens
        }

        for attempt in range(retries):
            try:
                await self.rate_limiter.acquire()

                if self.verbose:
                    print(f"  [ANALYSIS] Attempt {attempt + 1}/{retries}...")

                async with session.post(OPENROUTER_API_URL, headers=headers,
                                        json=payload, timeout=self.timeout) as resp:
                    if resp.status == 429:
                        wait = (2 ** attempt) * 5
                        print(f"  [RATE-LIMIT] Waiting {wait}s...")
                        await asyncio.sleep(wait)
                        continue

                    if resp.status != 200:
                        error = await resp.text()
                        raise Exception(f"API {resp.status}: {error[:200]}")

                    result = await resp.json()

                    if "choices" not in result or not result["choices"]:
                        raise Exception("Invalid API response: no choices")

                    if "message" not in result["choices"][0]:
                        raise Exception("Invalid API response: no message")

                    usage = result.get("usage", {})
                    self.stats["tokens_used"] += usage.get("total_tokens", 0)

                    content = result["choices"][0]["message"]["content"]
                    if not content or not content.strip():
                        raise Exception("API returned empty content")

                    return {"content": content, "usage": usage}

            except asyncio.TimeoutError:
                print(f"  [ANALYSIS-TIMEOUT] Attempt {attempt + 1}/{retries}")
                if attempt < retries - 1:
                    await asyncio.sleep((2 ** attempt) * 2)
            except Exception as e:
                print(f"  [ANALYSIS-ERROR] Attempt {attempt + 1}: {str(e)[:100]}")
                log_json(self.logger, "analysis_error", {
                    "keyword": keyword, "attempt": attempt + 1, "error": str(e)[:200]
                })
                if attempt < retries - 1:
                    await asyncio.sleep((2 ** attempt) * 2)

        print(f"  [ANALYSIS-FAILED] All {retries} attempts exhausted")
        return None

    def _apply_analysis(self, outline: str, analysis_yaml_str: str) -> Optional[str]:
        """Apply analysis decisions to produce a refined outline."""
        try:
            # Clean YAML fences if present
            cleaned = analysis_yaml_str.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r'^```\w*\n?', '', cleaned)
                cleaned = re.sub(r'\n?```$', '', cleaned)

            analysis = yaml.safe_load(cleaned)
            if not isinstance(analysis, list):
                return None

            # Build decision map: lowercase original text -> decision info
            decisions = {}
            for entry in analysis:
                text = entry.get("text", "").strip()
                if text:
                    decisions[text.lower()] = entry

            refined_lines = []
            for line in outline.split('\n'):
                stripped = line.strip()

                # Match heading tags
                match = re.match(r'<(h[1-4])[^>]*>(.*?)</\1>', stripped, re.IGNORECASE)
                if match:
                    level, text = match.group(1).lower(), match.group(2).strip()

                    # Always keep H1
                    if level == 'h1':
                        refined_lines.append(line)
                        continue

                    decision_info = decisions.get(text.lower())
                    if decision_info:
                        decision = decision_info.get("decision", "not_change")
                        if decision == "remove":
                            continue  # Skip removed headings
                        elif decision == "modify":
                            final = decision_info.get("final_decision", text)
                            refined_lines.append(f"<{level}>{final}</{level}>")
                        else:
                            refined_lines.append(line)
                    else:
                        # Not in analysis results, keep as is
                        refined_lines.append(line)
                else:
                    refined_lines.append(line)

            return '\n'.join(refined_lines).strip()
        except Exception as e:
            print(f"  [WARN] Failed to apply analysis: {e}")
            return None

    def estimate_cost(self, keyword_count: int) -> Dict[str, Any]:
        """Estimate API cost (generation + analysis passes)."""
        skip_analysis = getattr(self.args, 'skip_analysis', False)
        passes = 1 if skip_analysis else 2  # generation + analysis

        input_tokens = keyword_count * EST_INPUT_TOKENS * passes
        output_tokens = keyword_count * EST_OUTPUT_TOKENS * passes

        input_cost = (input_tokens / 1000) * COST_PER_1K_INPUT
        output_cost = (output_tokens / 1000) * COST_PER_1K_OUTPUT

        return {
            "keywords": keyword_count,
            "passes": passes,
            "est_input_tokens": input_tokens,
            "est_output_tokens": output_tokens,
            "est_input_cost": round(input_cost, 4),
            "est_output_cost": round(output_cost, 4),
            "est_total_cost": round(input_cost + output_cost, 4)
        }

    async def _call_api(self, session: aiohttp.ClientSession, keyword: str,
                        keyword_index: int, serp_data: Dict, query_csv: str,
                        retries: int = 3) -> Optional[Dict]:
        """Call OpenRouter API with retry logic."""

        # Build prompt variables
        language = self._detect_language(serp_data)
        variables = self._extract_prompt_variables(serp_data)
        serp_yaml = self._format_serp_yaml(serp_data)

        user_prompt = USER_PROMPT_TEMPLATE.format(
            keyword_index=keyword_index,
            keyword=keyword,
            source_context=SOURCE_CONTEXT,
            serp_analysis_yaml=serp_yaml,
            query_csv=query_csv[:2000],
            language=language,
            **variables
        )

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": HTTP_REFERER,
            "X-Title": GEN_X_TITLE
        }

        payload = {
            "model": self.args.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.args.temperature,
            "max_tokens": self.args.max_tokens
        }

        for attempt in range(retries):
            try:
                await self.rate_limiter.acquire()

                if self.verbose:
                    print(f"  [API] Attempt {attempt + 1}/{retries}...")

                async with session.post(OPENROUTER_API_URL, headers=headers,
                                        json=payload, timeout=self.timeout) as resp:
                    if resp.status == 429:
                        wait = (2 ** attempt) * 5
                        print(f"  [RATE-LIMIT] Waiting {wait}s...")
                        log_json(self.logger, "rate_limited", {
                            "keyword": keyword, "attempt": attempt + 1, "wait": wait
                        })
                        await asyncio.sleep(wait)
                        continue

                    if resp.status != 200:
                        error = await resp.text()
                        print(f"  [API-ERROR] Status {resp.status}: {error[:100]}")
                        raise Exception(f"API {resp.status}: {error[:200]}")

                    result = await resp.json()

                    # Validate response structure
                    if "choices" not in result or not result["choices"]:
                        print(f"  [API-ERROR] Invalid response structure: {str(result)[:100]}")
                        raise Exception("Invalid API response: no choices")

                    if "message" not in result["choices"][0]:
                        print(f"  [API-ERROR] No message in choice: {str(result['choices'][0])[:100]}")
                        raise Exception("Invalid API response: no message")

                    usage = result.get("usage", {})
                    self.stats["tokens_used"] += usage.get("total_tokens", 0)

                    content = result["choices"][0]["message"]["content"]
                    if not content or not content.strip():
                        print(f"  [API-ERROR] Empty content returned")
                        raise Exception("API returned empty content")

                    return {
                        "content": content,
                        "usage": usage
                    }

            except asyncio.TimeoutError:
                print(f"  [TIMEOUT] Attempt {attempt + 1}/{retries}")
                log_json(self.logger, "timeout", {"keyword": keyword, "attempt": attempt + 1})
                if attempt < retries - 1:
                    await asyncio.sleep((2 ** attempt) * 2)
            except aiohttp.ClientError as e:
                print(f"  [NETWORK-ERROR] {type(e).__name__}: {str(e)[:100]}")
                log_json(self.logger, "api_error", {
                    "keyword": keyword, "attempt": attempt + 1, "error": str(e)[:200]
                })
                if attempt < retries - 1:
                    await asyncio.sleep((2 ** attempt) * 2)
            except Exception as e:
                print(f"  [ERROR] Attempt {attempt + 1}: {str(e)[:100]}")
                log_json(self.logger, "api_error", {
                    "keyword": keyword, "attempt": attempt + 1, "error": str(e)[:200]
                })
                if attempt < retries - 1:
                    await asyncio.sleep((2 ** attempt) * 2)

        print(f"  [FAILED] All {retries} attempts exhausted")
        return None

    async def generate_outline(self, session: aiohttp.ClientSession,
                               keyword: str, keyword_index: int) -> bool:
        """Generate outline for a single keyword."""
        async with self.semaphore:
            try:
                if self.verbose:
                    print(f"\n[{keyword_index}] Processing: {keyword}")

                force = getattr(self.args, 'force', False)

                # Skip if completed (unless --force)
                if keyword in self.checkpoint["completed"] and not force:
                    print(f"  [SKIP] {keyword}: already in checkpoint completed list")
                    self.stats["skipped"] += 1
                    return True

                # Define output path early
                keyword_dir = self.output_dir / keyword
                output_path = keyword_dir / f"{keyword}-outline-optimized.md"

                if self.verbose:
                    print(f"  [OUTPUT] Target: {output_path}")

                # Skip if output exists (incremental mode, unless --force)
                if self.args.incremental and output_path.exists() and not force:
                    print(f"  [SKIP] {keyword}: output file already exists ({output_path})")
                    self.stats["skipped"] += 1
                    return True

                # Ensure keyword directory exists
                keyword_dir.mkdir(parents=True, exist_ok=True)

                # Load SERP analysis (input)
                serp_data = self._load_serp_analysis(keyword)
                if not serp_data:
                    print(f"  [SKIP] {keyword}: no SERP analysis file found")
                    log_json(self.logger, "skipped", {
                        "keyword": keyword, "reason": "no_serp_analysis"
                    })
                    self.stats["skipped"] += 1
                    return False

                # Load master queries (input)
                query_csv = self._load_master_queries(keyword)
                if self.verbose:
                    has_queries = query_csv != "No query data available."
                    print(f"  [QUERIES] Available: {has_queries}")

                # Dry run - validate inputs only
                if self.args.dry_run:
                    print(f"  [DRY-RUN] Would generate outline for: {keyword}")
                    log_json(self.logger, "dry_run", {
                        "keyword": keyword,
                        "index": keyword_index,
                        "has_serp": True,
                        "has_queries": query_csv != "No query data available.",
                        "language": self._detect_language(serp_data)
                    })
                    self.stats["success"] += 1
                    return True

                # Call API
                if self.verbose:
                    print(f"  [API] Calling OpenRouter ({self.args.model})...")

                result = await self._call_api(session, keyword, keyword_index,
                                             serp_data, query_csv)

                if not result:
                    print(f"  [FAILED] API call failed for: {keyword}")
                    if keyword not in self.checkpoint["failed"]:
                        self.checkpoint["failed"].append(keyword)
                    self.stats["failed"] += 1
                    return False

                if self.verbose:
                    print(f"  [API] Response received ({result['usage'].get('total_tokens', 0)} tokens)")

                # Clean and validate output
                outline = self._clean_outline(result["content"])
                is_valid, issues, is_structural_failure = self._validate_outline(outline)

                if issues:
                    print(f"  [WARN] Validation issues: {', '.join(issues)}")
                    log_json(self.logger, "validation", {
                        "keyword": keyword, "issues": issues, "valid": is_valid,
                        "structural_failure": is_structural_failure
                    })
                    self.stats["validation_warnings"] += len(issues)

                # Structural failure = hard reject, do not save
                if is_structural_failure:
                    print(f"  [REJECTED] {keyword}: headline count outside 25-30 range")
                    log_json(self.logger, "structural_failure", {
                        "keyword": keyword, "issues": issues
                    })
                    self.stats["structural_failures"] += 1
                    if keyword not in self.checkpoint["failed"]:
                        self.checkpoint["failed"].append(keyword)
                    self.stats["failed"] += 1
                    return False

                # Save output
                try:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(outline)
                    print(f"  [SAVED] {output_path}")
                except Exception as e:
                    print(f"  [ERROR] Failed to save output: {e}")
                    raise

                # Run outline analysis (post-generation evaluation)
                if not getattr(self.args, 'skip_analysis', False):
                    if self.verbose:
                        print(f"  [ANALYSIS] Running outline analysis...")

                    analysis_result = await self._analyze_outline(
                        session, keyword, keyword_index, outline
                    )

                    if analysis_result:
                        # Save analysis YAML
                        analysis_path = keyword_dir / f"{keyword}-outline-analysis.yaml"
                        try:
                            with open(analysis_path, 'w', encoding='utf-8') as f:
                                f.write(analysis_result["content"])
                            print(f"  [SAVED] {analysis_path}")
                        except Exception as e:
                            print(f"  [WARN] Failed to save analysis: {e}")

                        # Apply modifications to create refined outline
                        refined = self._apply_analysis(outline, analysis_result["content"])
                        if refined:
                            refined_path = keyword_dir / f"{keyword}-outline-refined.md"
                            try:
                                with open(refined_path, 'w', encoding='utf-8') as f:
                                    f.write(refined)
                                print(f"  [SAVED] {refined_path}")
                            except Exception as e:
                                print(f"  [WARN] Failed to save refined outline: {e}")

                        self.stats["analysis_success"] += 1
                        log_json(self.logger, "analysis_success", {
                            "keyword": keyword, "index": keyword_index,
                            "tokens": analysis_result["usage"].get("total_tokens", 0)
                        })
                    else:
                        self.stats["analysis_failed"] += 1
                        log_json(self.logger, "analysis_failed", {
                            "keyword": keyword, "index": keyword_index
                        })

                self.checkpoint["completed"].append(keyword)
                self.stats["success"] += 1

                log_json(self.logger, "success", {
                    "keyword": keyword,
                    "index": keyword_index,
                    "h1": len(re.findall(r'<h1', outline, re.IGNORECASE)),
                    "h2": len(re.findall(r'<h2', outline, re.IGNORECASE)),
                    "h3": len(re.findall(r'<h3', outline, re.IGNORECASE)),
                    "tokens": result["usage"].get("total_tokens", 0),
                    "valid": is_valid
                })

                return True

            except Exception as e:
                print(f"  [ERROR] {keyword}: {str(e)[:100]}")
                log_json(self.logger, "error", {
                    "keyword": keyword, "error": str(e)[:200]
                })
                if keyword not in self.checkpoint["failed"]:
                    self.checkpoint["failed"].append(keyword)
                    self.stats["failed"] += 1
                return False

    def _validate_inputs(self, keywords: List[str]) -> Dict[str, Any]:
        """Pre-validate which keywords have required input files."""
        valid = []
        missing_serp = []

        for kw in keywords:
            serp_file = self.output_dir / kw / f"{kw}-serp-analysis.yaml"
            if serp_file.exists():
                valid.append(kw)
            else:
                missing_serp.append(kw)

        return {
            "valid": valid,
            "missing_serp": missing_serp,
            "valid_count": len(valid),
            "missing_count": len(missing_serp)
        }

    async def run(self):
        """Run the outline generation pipeline."""
        # Load keywords
        keywords_path = Path(self.args.file)
        if not keywords_path.exists():
            print(f"Error: Keywords file not found: {self.args.file}")
            print(f"  Expected path: {keywords_path.absolute()}")
            return

        with open(keywords_path, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        if not keywords:
            print("Error: No keywords found in file")
            return

        self.stats["total"] = len(keywords)

        # Resume from checkpoint
        if self.args.resume_from:
            try:
                start_idx = int(self.args.resume_from)
                keywords = keywords[start_idx:]
                print(f"Resuming from index {start_idx}")
            except ValueError:
                pass

        # Cost estimation mode
        if self.args.estimate_cost:
            est = self.estimate_cost(len(keywords))
            print("\n" + "=" * 55)
            print("  Phase 3.1: Outline Generation - Cost Estimate")
            print("=" * 55)
            print(f"  Keywords to process:    {est['keywords']:,}")
            print(f"  API passes per keyword: {est['passes']} ({'generation only' if est['passes'] == 1 else 'generation + analysis'})")
            print(f"  Est. input tokens:      {est['est_input_tokens']:,}")
            print(f"  Est. output tokens:     {est['est_output_tokens']:,}")
            print(f"  Est. input cost:        ${est['est_input_cost']:.4f}")
            print(f"  Est. output cost:       ${est['est_output_cost']:.4f}")
            print(f"  Est. TOTAL cost:        ${est['est_total_cost']:.4f}")
            print("=" * 55)
            return

        # Pre-validate inputs
        validation = self._validate_inputs(keywords)
        if self.verbose:
            print(f"\n[VALIDATION] Keywords with SERP data: {validation['valid_count']}/{len(keywords)}")
            if validation['missing_serp']:
                print(f"[VALIDATION] Missing SERP analysis for: {', '.join(validation['missing_serp'][:5])}")
                if len(validation['missing_serp']) > 5:
                    print(f"             ... +{len(validation['missing_serp']) - 5} more")

        if validation['valid_count'] == 0:
            print("\nError: No keywords have SERP analysis data available.")
            print(f"  Looking in: {self.output_dir.absolute()}")
            print(f"  Expected structure: {self.output_dir}/{{keyword}}/{{keyword}}-serp-analysis.yaml")
            return

        log_json(self.logger, "started", {
            "total": len(keywords),
            "valid_inputs": validation['valid_count'],
            "concurrency": self.args.max_concurrency,
            "model": self.args.model,
            "dry_run": self.args.dry_run,
            "incremental": self.args.incremental
        })

        print(f"\n{'='*55}")
        print("  Phase 3.1: SEO Outline Generation")
        print(f"{'='*55}")
        print(f"  Keywords: {len(keywords)} | Valid inputs: {validation['valid_count']}")
        print(f"  Concurrency: {self.args.max_concurrency}")
        print(f"  Model: {self.args.model}")
        print(f"  Mode: {'DRY RUN' if self.args.dry_run else 'LIVE'}")
        print(f"  Force: {'YES' if getattr(self.args, 'force', False) else 'NO'}")
        print(f"  Analysis: {'SKIP' if getattr(self.args, 'skip_analysis', False) else 'ENABLED'}")
        print(f"  Output: {self.output_dir.absolute()}")
        print(f"{'='*55}\n")

        async with aiohttp.ClientSession() as session:
            # Process in chunks for checkpointing
            for chunk_start in range(0, len(keywords), self.args.chunk_size):
                chunk_end = min(chunk_start + self.args.chunk_size, len(keywords))
                chunk = keywords[chunk_start:chunk_end]

                print(f"Processing chunk {chunk_start+1}-{chunk_end} of {len(keywords)}...")

                # Create tasks with indices
                tasks = [
                    self.generate_outline(session, kw, chunk_start + i + 1)
                    for i, kw in enumerate(chunk)
                ]

                # Process concurrently
                await asyncio.gather(*tasks, return_exceptions=True)

                # Save checkpoint after each chunk
                self.checkpoint["last_index"] = chunk_end
                self._save_checkpoint()

                log_json(self.logger, "chunk_done", {
                    "end": chunk_end,
                    "success": self.stats["success"],
                    "failed": self.stats["failed"]
                })

        # Final summary
        log_json(self.logger, "completed", self.stats)

        print(f"\n{'='*55}")
        print("  Outline Generation Complete")
        print(f"{'='*55}")
        print(f"  Total:      {self.stats['total']}")
        print(f"  Success:    {self.stats['success']}")
        print(f"  Failed:     {self.stats['failed']}")
        print(f"  Structural: {self.stats['structural_failures']}")
        print(f"  Skipped:    {self.stats['skipped']}")
        print(f"  Tokens:     {self.stats['tokens_used']:,}")
        print(f"  Warnings:   {self.stats['validation_warnings']}")
        if not getattr(self.args, 'skip_analysis', False):
            print(f"  Analysis OK:{self.stats['analysis_success']}")
            print(f"  Analysis NG:{self.stats['analysis_failed']}")
        print(f"{'='*55}")

        if self.checkpoint["failed"]:
            print(f"\nFailed keywords: {', '.join(self.checkpoint['failed'][:5])}")
            if len(self.checkpoint["failed"]) > 5:
                print(f"  ... +{len(self.checkpoint['failed']) - 5} more")


def parse_args():
    """Parse CLI arguments matching HTML specification."""
    parser = argparse.ArgumentParser(
        description="Phase 3.1: Koray-aligned SEO Outline Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run scripts/outline_generation.py --dry-run
  uv run scripts/outline_generation.py --estimate-cost
  uv run scripts/outline_generation.py --incremental
  uv run scripts/outline_generation.py --max-concurrency=5
  uv run scripts/outline_generation.py --resume-from=100
  uv run scripts/outline_generation.py --verbose
        """
    )

    parser.add_argument("--file", default=KEYWORDS_FILE,
                        help=f"Keywords file path (default: {KEYWORDS_FILE})")
    parser.add_argument("--max-concurrency", type=int, default=DEFAULT_MAX_CONCURRENCY,
                        help=f"Parallel OpenRouter API calls (default: {DEFAULT_MAX_CONCURRENCY})")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE,
                        help=f"Keywords per checkpoint chunk (default: {DEFAULT_CHUNK_SIZE})")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                        help=f"HTTP timeout for each request (default: {DEFAULT_TIMEOUT}s)")
    parser.add_argument("--model", default=DEFAULT_MODEL,
                        help=f"OpenRouter model (default: {DEFAULT_MODEL})")
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE,
                        help=f"LLM temperature (default: {DEFAULT_TEMPERATURE})")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS,
                        help=f"Max output tokens (default: {DEFAULT_MAX_TOKENS})")
    parser.add_argument("--incremental", action="store_true",
                        help="Skip existing outputs (incremental mode)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate inputs without API calls")
    parser.add_argument("--estimate-cost", action="store_true",
                        help="Estimate cost before running")
    parser.add_argument("--resume-from", type=str,
                        help="Continue from last checkpoint index")
    parser.add_argument("--skip-analysis", action="store_true",
                        help="Skip outline analysis phase (generate only)")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing outputs and ignore checkpoint completed list")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose output for debugging")

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    if not API_KEY or API_KEY == "your_api_key_here":
        print("Error: Set OPENROUTER_API_KEY environment variable")
        return

    generator = OutlineGenerator(args)
    await generator.run()


if __name__ == "__main__":
    asyncio.run(main())