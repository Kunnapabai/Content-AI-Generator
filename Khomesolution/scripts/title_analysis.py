import asyncio
import yaml
import json
import os
import argparse
import logging
import time
from datetime import datetime
from pathlib import Path
from aiohttp import ClientSession, ClientTimeout
from typing import List, Dict, Optional, Any

from config_loader import get_openrouter_config, get_model_config, load_prompt

# --- Configuration (loaded from config.yaml) ---
_or_cfg = get_openrouter_config()
_model_cfg = get_model_config("title_analysis")

OPENROUTER_API_KEY = _or_cfg["api_key"]
OPENROUTER_API_URL = _or_cfg["api_url"]
HTTP_REFERER = _or_cfg["http_referer"]
MODEL = _model_cfg["model"]
MAX_CONCURRENCY = _model_cfg.get("max_concurrency", 10)
TEMPERATURE = _model_cfg.get("temperature", 0.2)
MAX_TOKENS = _model_cfg.get("max_tokens", 8000)
TIMEOUT_SECONDS = _model_cfg.get("timeout", 90)
CHUNK_SIZE = _model_cfg.get("chunk_size", 500)
QUALITY_THRESHOLD = _model_cfg.get("quality_threshold", 0.7)
X_TITLE = _model_cfg.get("x_title", "Privato Content SERP Analyzer")

OUTPUT_DIR = "output/research"
KEYWORDS_FILE = "data/keywords/keywords.txt"
CHECKPOINT_DIR = "checkpoints"
CHECKPOINT_FILE = "title_analysis_checkpoint.json"
LOG_DIR = "logs"
LOG_FILE = "llm_analysis.log"

# Rate limiting
RATE_LIMIT_RPM = _model_cfg.get("rate_limit_rpm", 60)
RATE_LIMIT_TPM = 60000

# Predicate types for Knowledge Graph (TITLE-FOCUSED LEAN)
VALID_PREDICATES = [
    "is_a", "aka", "related_to", "has_attribute", "has_quantity",
    "has_duration", "has_cost", "has_benefit", "has_risk", "requires",
    "time_to_result", "compared_with", "alternative_to", "suitable_for",
    "defined_as", "available_at"
]

# --- System & User Prompts (loaded from PROMPTS/) ---
SYSTEM_PROMPT = load_prompt("title_analysis_system.md")
USER_PROMPT_TEMPLATE = load_prompt("title_analysis_user.md")


def setup_logging():
    """Setup JSON lines logging."""
    Path(LOG_DIR).mkdir(parents=True, exist_ok=True)

    # Create a custom handler for JSON lines format
    log_path = Path(LOG_DIR) / LOG_FILE

    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def log_json(logger, event: str, data: Dict[str, Any]):
    """Log event as JSON line."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event": event,
        **data
    }
    logger.info(json.dumps(log_entry, ensure_ascii=False))


def load_checkpoint() -> Dict[str, Any]:
    """Load checkpoint file if exists."""
    checkpoint_path = Path(CHECKPOINT_DIR) / CHECKPOINT_FILE
    if checkpoint_path.exists():
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"completed": [], "failed": [], "last_index": 0}


def save_checkpoint(checkpoint: Dict[str, Any]):
    """Save checkpoint file."""
    Path(CHECKPOINT_DIR).mkdir(parents=True, exist_ok=True)
    checkpoint_path = Path(CHECKPOINT_DIR) / CHECKPOINT_FILE
    checkpoint["updated_at"] = datetime.now().isoformat()
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)


def load_keywords(keywords_file: str) -> List[str]:
    """Load keywords from file."""
    with open(keywords_file, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]


def scan_keywords_from_output_dir(output_dir: str = OUTPUT_DIR) -> List[str]:
    """Scan subdirectories in OUTPUT_DIR to get keywords.

    Each subdirectory name is treated as a keyword.
    Only includes directories that have the required input files.
    """
    output_path = Path(output_dir)
    if not output_path.exists():
        return []

    keywords = []
    for item in output_path.iterdir():
        if item.is_dir():
            keyword = item.name
            # Check if directory has required input files (competitions.json or keywords.json)
            comp_file = item / f"{keyword}-competitions.json"
            kw_file = item / f"{keyword}-keywords.json"

            if comp_file.exists() or kw_file.exists():
                keywords.append(keyword)

    # Sort for consistent ordering
    return sorted(keywords)


def load_serp_data(keyword: str, verbose: bool = False) -> Dict[str, Any]:
    """Load dual SERP JSON inputs for a keyword.

    Returns dict with 'competitions', 'keywords', and 'debug' info.
    """
    keyword_dir = Path(OUTPUT_DIR) / keyword
    debug_info = {
        "keyword_dir": str(keyword_dir.absolute()),
        "comp_path": None,
        "comp_status": None,
        "kw_path": None,
        "kw_status": None
    }

    # Load competitions.json
    comp_path = keyword_dir / f"{keyword}-competitions.json"
    debug_info["comp_path"] = str(comp_path.absolute())
    competitions = {}

    if comp_path.exists():
        try:
            with open(comp_path, 'r', encoding='utf-8') as f:
                competitions = json.load(f)
            debug_info["comp_status"] = "loaded"
            if verbose:
                print(f"  [INPUT] Loaded: {comp_path.absolute()}")
        except json.JSONDecodeError as e:
            debug_info["comp_status"] = f"json_error: {str(e)[:50]}"
            if verbose:
                print(f"  [ERROR] JSON decode error in: {comp_path.absolute()}")
                print(f"          {e}")
    else:
        debug_info["comp_status"] = "not_found"
        if verbose:
            print(f"  [MISSING] File not found: {comp_path.absolute()}")

    # Load keywords.json
    kw_path = keyword_dir / f"{keyword}-keywords.json"
    debug_info["kw_path"] = str(kw_path.absolute())
    keywords_data = {}

    if kw_path.exists():
        try:
            with open(kw_path, 'r', encoding='utf-8') as f:
                keywords_data = json.load(f)
            debug_info["kw_status"] = "loaded"
            if verbose:
                print(f"  [INPUT] Loaded: {kw_path.absolute()}")
        except json.JSONDecodeError as e:
            debug_info["kw_status"] = f"json_error: {str(e)[:50]}"
            if verbose:
                print(f"  [ERROR] JSON decode error in: {kw_path.absolute()}")
                print(f"          {e}")
    else:
        debug_info["kw_status"] = "not_found"
        if verbose:
            print(f"  [MISSING] File not found: {kw_path.absolute()}")

    return {
        "competitions": competitions,
        "keywords": keywords_data,
        "debug": debug_info
    }


def format_competitors_data(competitions) -> str:
    """Format competitor data for prompt."""
    # Handle both list and dict input formats
    if isinstance(competitions, list):
        organic = competitions
    elif isinstance(competitions, dict):
        organic = competitions.get("organic", competitions.get("items", []))
    else:
        organic = []

    if not organic:
        return "No competitor data available."

    lines = []
    for i, item in enumerate(organic[:10], 1):
        title = item.get("title", "N/A")
        snippet = item.get("snippet", item.get("description", "N/A"))
        url = item.get("url", item.get("link", "N/A"))
        lines.append(f"{i}. Title: {title}")
        lines.append(f"   Snippet: {snippet}")
        lines.append(f"   URL: {url}")
        lines.append("")

    return "\n".join(lines)


def format_related_keywords(keywords_data: Dict) -> str:
    """Format related keywords for prompt."""
    related = keywords_data.get("related_keywords", keywords_data.get("related", []))
    if not related:
        return "No related keywords available."

    if isinstance(related[0], dict):
        return "\n".join([f"- {kw.get('keyword', kw.get('query', str(kw)))}" for kw in related[:20]])
    return "\n".join([f"- {kw}" for kw in related[:20]])


def format_paa_questions(keywords_data: Dict) -> str:
    """Format PAA questions for prompt."""
    paa = keywords_data.get("people_also_ask", keywords_data.get("paa", []))
    if not paa:
        return "No PAA questions available."

    if isinstance(paa[0], dict):
        return "\n".join([f"- {q.get('question', q.get('query', str(q)))}" for q in paa[:10]])
    return "\n".join([f"- {q}" for q in paa[:10]])


def strip_yaml_fences(content: str) -> str:
    """Remove markdown code fences from YAML content."""
    content = content.strip()
    if content.startswith("```yaml"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def sanitize_yaml_content(content: str) -> str:
    """Sanitize YAML content to handle common LLM output issues.

    Aggressively quotes all string values to prevent YAML parsing errors
    from colons, special characters, and non-ASCII text.
    """
    import re

    lines = content.split('\n')
    sanitized_lines = []

    # Special YAML values that should not be quoted
    yaml_special = {'true', 'false', 'null', '~', 'yes', 'no', 'on', 'off'}

    for line in lines:
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            sanitized_lines.append(line)
            continue

        # Skip lines that are just a key with no value (like "meta:")
        if stripped.endswith(':') and ': ' not in stripped:
            sanitized_lines.append(line)
            continue

        # Find the first ": " which separates key from value
        # This handles Unicode keys properly
        colon_pos = line.find(': ')
        if colon_pos > 0:
            key_part = line[:colon_pos + 1]  # includes the colon
            value_part = line[colon_pos + 2:]  # after ": "
            value = value_part.rstrip()

            # Skip if empty value
            if not value:
                sanitized_lines.append(line)
                continue

            # Check if value is already properly quoted
            if (value.startswith('"') and value.endswith('"') and len(value) > 1) or \
               (value.startswith("'") and value.endswith("'") and len(value) > 1):
                sanitized_lines.append(line)
                continue

            # Skip special YAML values
            if value.lower() in yaml_special:
                sanitized_lines.append(line)
                continue

            # Skip numbers (int, float, scientific notation)
            if re.match(r'^-?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$', value):
                sanitized_lines.append(line)
                continue

            # Skip if value starts with [ or { (inline arrays/objects)
            if value.startswith('[') or value.startswith('{'):
                sanitized_lines.append(line)
                continue

            # Skip block scalar indicators
            if value in ('|', '>', '|-', '>-', '|+', '>+'):
                sanitized_lines.append(line)
                continue

            # Quote everything else to be safe
            escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
            sanitized_lines.append(f'{key_part} "{escaped_value}"')

        # Handle list items (- value)
        elif stripped.startswith('- '):
            # Find where "- " starts
            dash_pos = line.find('- ')
            indent = line[:dash_pos]
            value = line[dash_pos + 2:].rstrip()

            # Skip empty
            if not value:
                sanitized_lines.append(line)
                continue

            # Check if it's a key-value pair within the list item (- key: value)
            inner_colon = value.find(': ')
            if inner_colon > 0:
                inner_key = value[:inner_colon]
                inner_value = value[inner_colon + 2:]

                # Skip if already quoted or special
                if (inner_value.startswith('"') and inner_value.endswith('"')) or \
                   (inner_value.startswith("'") and inner_value.endswith("'")) or \
                   inner_value.lower() in yaml_special or \
                   re.match(r'^-?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$', inner_value) or \
                   inner_value.startswith('[') or inner_value.startswith('{'):
                    sanitized_lines.append(line)
                    continue

                escaped_value = inner_value.replace('\\', '\\\\').replace('"', '\\"')
                sanitized_lines.append(f'{indent}- {inner_key}: "{escaped_value}"')
            else:
                # Plain list item value
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")):
                    sanitized_lines.append(line)
                    continue

                # Quote if contains problematic characters
                if ':' in value or '#' in value or any(ord(c) > 127 for c in value):
                    escaped_value = value.replace('\\', '\\\\').replace('"', '\\"')
                    sanitized_lines.append(f'{indent}- "{escaped_value}"')
                else:
                    sanitized_lines.append(line)
        else:
            sanitized_lines.append(line)

    return '\n'.join(sanitized_lines)


def extract_yaml_sections(content: str) -> Optional[Dict]:
    """Extract YAML sections manually as a last resort fallback.

    Parses the content section by section to salvage what we can.
    """
    import re

    required_sections = [
        "meta", "intent", "ymyl", "lexical_signals", "pattern_signals",
        "entity_signals", "knowledge_graph", "competitor_matrix",
        "paa_and_related", "consensus_signals", "opportunity_gaps",
        "title_generation_signals"
    ]

    result = {}

    # Try to find each section and extract its content
    for i, section in enumerate(required_sections):
        # Pattern to match section start
        pattern = rf'^{section}:\s*$'
        lines = content.split('\n')

        section_start = None
        for idx, line in enumerate(lines):
            if re.match(pattern, line.strip()):
                section_start = idx
                break

        if section_start is not None:
            # Find next section or end
            section_end = len(lines)
            for next_section in required_sections[i + 1:]:
                for idx in range(section_start + 1, len(lines)):
                    if re.match(rf'^{next_section}:\s*$', lines[idx].strip()):
                        section_end = idx
                        break
                if section_end != len(lines):
                    break

            # Extract section content
            section_lines = lines[section_start + 1:section_end]
            section_content = '\n'.join([section] + [':'] + section_lines)

            try:
                parsed = yaml.safe_load(f"{section}:\n" + '\n'.join(section_lines))
                if parsed and section in parsed:
                    result[section] = parsed[section]
            except yaml.YAMLError:
                # Store raw content as fallback
                result[section] = {"_raw": '\n'.join(section_lines)}

    return result if result else None


def safe_yaml_load(content: str, keyword: str = "", logger=None) -> Optional[Dict]:
    """Safely load YAML with multiple fallback strategies."""
    errors = []

    # Strategy 1: Direct parse
    try:
        data = yaml.safe_load(content)
        if isinstance(data, dict):
            return data
    except yaml.YAMLError as e:
        errors.append(f"Direct parse: {str(e)[:100]}")

    # Strategy 2: Sanitize and retry
    try:
        sanitized = sanitize_yaml_content(content)
        data = yaml.safe_load(sanitized)
        if isinstance(data, dict):
            return data
    except yaml.YAMLError as e:
        errors.append(f"Sanitized parse: {str(e)[:100]}")

    # Strategy 3: Try JSON (LLM might output JSON instead)
    try:
        data = json.loads(content)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError as e:
        errors.append(f"JSON parse: {str(e)[:100]}")

    # Strategy 4: Section-by-section extraction
    try:
        data = extract_yaml_sections(content)
        if data and len(data) >= 6:  # At least half the sections
            return data
    except Exception as e:
        errors.append(f"Section extraction: {str(e)[:100]}")

    # Save raw content for debugging if all strategies fail
    if keyword:
        debug_dir = Path(OUTPUT_DIR) / keyword
        debug_dir.mkdir(parents=True, exist_ok=True)
        debug_file = debug_dir / f"{keyword}-raw-response.txt"
        try:
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"# Parse errors:\n")
                for err in errors:
                    f.write(f"# - {err}\n")
                f.write(f"\n# Raw content:\n{content}")
        except Exception:
            pass

    return None


def validate_yaml_schema(data: Dict) -> tuple[bool, List[str]]:
    """Validate YAML against expected schema."""
    required_sections = [
        "meta", "intent", "ymyl", "lexical_signals", "pattern_signals",
        "entity_signals", "knowledge_graph", "competitor_matrix",
        "paa_and_related", "consensus_signals", "opportunity_gaps",
        "title_generation_signals"
    ]

    errors = []

    # Check required sections
    for section in required_sections:
        if section not in data:
            errors.append(f"Missing required section: {section}")

    # Validate knowledge_graph constraints
    if "knowledge_graph" in data:
        kg = data["knowledge_graph"]
        nodes = kg.get("nodes", [])
        edges = kg.get("edges", [])

        if len(nodes) > 12:
            errors.append(f"Knowledge graph has {len(nodes)} nodes (max 12)")
        if len(edges) > 18:
            errors.append(f"Knowledge graph has {len(edges)} edges (max 18)")

        # Validate predicate values
        for edge in edges:
            pred = edge.get("predicate", "")
            if pred and pred not in VALID_PREDICATES:
                errors.append(f"Invalid predicate: {pred}")

    # Validate entity_signals constraint (new schema: entities nested under entities key)
    if "entity_signals" in data:
        entities = data["entity_signals"]
        if isinstance(entities, dict):
            entity_list = entities.get("entities", [])
            if isinstance(entity_list, list) and len(entity_list) > 8:
                errors.append(f"Entity signals has {len(entity_list)} entities (max 8)")
        elif isinstance(entities, list) and len(entities) > 8:
            errors.append(f"Entity signals has {len(entities)} entities (max 8)")

    # Validate opportunity_gaps constraint (max 3)
    if "opportunity_gaps" in data:
        gaps = data["opportunity_gaps"]
        if isinstance(gaps, list) and len(gaps) > 3:
            errors.append(f"Opportunity gaps has {len(gaps)} entries (max 3)")

    # Validate dominant_title_patterns constraint (max 2)
    if "pattern_signals" in data:
        ps = data["pattern_signals"]
        if isinstance(ps, dict):
            patterns = ps.get("dominant_title_patterns", [])
            if isinstance(patterns, list) and len(patterns) > 2:
                errors.append(f"Dominant title patterns has {len(patterns)} entries (max 2)")

    return len(errors) == 0, errors


def calculate_quality_score(data: Dict) -> float:
    """Calculate quality score based on completeness and validity."""
    score = 0.0
    max_score = 12.0  # One point per section

    required_sections = [
        "meta", "intent", "ymyl", "lexical_signals", "pattern_signals",
        "entity_signals", "knowledge_graph", "competitor_matrix",
        "paa_and_related", "consensus_signals", "opportunity_gaps",
        "title_generation_signals"
    ]

    for section in required_sections:
        if section in data and data[section]:
            score += 1.0

    # Bonus for knowledge graph quality
    if "knowledge_graph" in data:
        kg = data["knowledge_graph"]
        if kg.get("nodes") and kg.get("edges"):
            score += 0.5
        if kg.get("central_concepts"):
            score += 0.25

    # Bonus for entity signals quality (new schema: entities nested)
    if "entity_signals" in data and data["entity_signals"]:
        es = data["entity_signals"]
        if isinstance(es, dict) and es.get("entities"):
            score += 0.5
        elif isinstance(es, list) and es:
            score += 0.5

    # Bonus for evidence coverage
    if "pattern_signals" in data:
        ps = data["pattern_signals"]
        if isinstance(ps, dict) and ps.get("angles_observed"):
            score += 0.25

    return min(score / (max_score + 1.5), 1.0)


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, rpm: int = 60):
        self.rpm = rpm
        self.interval = 60.0 / rpm
        self.last_call = 0.0
        self.lock = asyncio.Lock()

    async def acquire(self):
        async with self.lock:
            now = time.time()
            wait_time = self.last_call + self.interval - now
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self.last_call = time.time()


class SERPAnalyzer:
    """SERP Semantic Analyzer using Grok-4 via OpenRouter."""

    def __init__(self, args):
        self.args = args
        self.semaphore = asyncio.Semaphore(args.max_concurrency)
        self.rate_limiter = RateLimiter(RATE_LIMIT_RPM)
        self.logger = setup_logging()
        self.checkpoint = load_checkpoint()
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "total_tokens": 0
        }

    async def call_openrouter(self, session: ClientSession, keyword: str,
                               serp_data: Dict, retry_count: int = 3) -> Optional[Dict]:
        """Call OpenRouter API with retry logic."""

        # Format prompt data
        competitors_text = format_competitors_data(serp_data.get("competitions", {}))
        related_text = format_related_keywords(serp_data.get("keywords", {}))
        paa_text = format_paa_questions(serp_data.get("keywords", {}))

        user_prompt = USER_PROMPT_TEMPLATE.format(
            keyword=keyword,
            competitors_data=competitors_text,
            related_keywords=related_text,
            paa_questions=paa_text
        )

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": HTTP_REFERER,
            "X-Title": X_TITLE
        }

        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": self.args.temperature,
            "max_tokens": self.args.max_tokens
        }

        for attempt in range(retry_count):
            try:
                await self.rate_limiter.acquire()

                async with session.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=ClientTimeout(total=self.args.timeout)
                ) as resp:
                    if resp.status == 429:
                        # Rate limited - exponential backoff
                        wait_time = (2 ** attempt) * 5
                        log_json(self.logger, "rate_limited", {
                            "keyword": keyword,
                            "attempt": attempt + 1,
                            "wait_seconds": wait_time
                        })
                        await asyncio.sleep(wait_time)
                        continue

                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"API error {resp.status}: {error_text}")

                    result = await resp.json()

                    # Track token usage
                    usage = result.get("usage", {})
                    self.stats["total_tokens"] += usage.get("total_tokens", 0)

                    content = result["choices"][0]["message"]["content"]
                    return {"content": content, "usage": usage}

            except asyncio.TimeoutError:
                log_json(self.logger, "timeout", {
                    "keyword": keyword,
                    "attempt": attempt + 1
                })
                if attempt < retry_count - 1:
                    await asyncio.sleep((2 ** attempt) * 2)
            except Exception as e:
                log_json(self.logger, "api_error", {
                    "keyword": keyword,
                    "attempt": attempt + 1,
                    "error": str(e)
                })
                if attempt < retry_count - 1:
                    await asyncio.sleep((2 ** attempt) * 2)

        return None

    async def analyze_keyword(self, session: ClientSession, keyword: str) -> bool:
        """Analyze a single keyword."""
        verbose = getattr(self.args, 'verbose', False)

        try:
            async with self.semaphore:
                if verbose:
                    print(f"\n[PROCESSING] Keyword: {keyword}")

                # Check if output file already exists on disk (skip unless --force is set)
                output_path = Path(OUTPUT_DIR) / keyword / f"{keyword}-serp-analysis.yaml"
                if verbose:
                    print(f"  [OUTPUT] Target: {output_path.absolute()}")

                if not self.args.force and output_path.exists():
                    print(f"  [SKIP] Output already exists: {output_path.absolute()}")
                    self.stats["skipped"] += 1
                    log_json(self.logger, "skipped", {"keyword": keyword, "reason": "output_exists"})
                    return True

                # Load SERP data with verbose output
                serp_data = load_serp_data(keyword, verbose=verbose)
                debug = serp_data.get("debug", {})

                if not serp_data["competitions"] and not serp_data["keywords"]:
                    # Print specific reasons for missing data
                    print(f"  [SKIP] No input data found for: {keyword}")
                    print(f"         Keyword dir: {debug.get('keyword_dir', 'N/A')}")
                    print(f"         competitions.json: {debug.get('comp_status', 'N/A')}")
                    print(f"           Path: {debug.get('comp_path', 'N/A')}")
                    print(f"         keywords.json: {debug.get('kw_status', 'N/A')}")
                    print(f"           Path: {debug.get('kw_path', 'N/A')}")

                    log_json(self.logger, "skipped", {
                        "keyword": keyword,
                        "reason": "no_serp_data",
                        "debug": debug
                    })
                    self.stats["skipped"] += 1
                    return False

            # Dry run mode - just estimate
            if self.args.dry_run:
                log_json(self.logger, "dry_run", {
                    "keyword": keyword,
                    "estimated_tokens": 5000  # Rough estimate
                })
                return True

            # Call API
            result = await self.call_openrouter(session, keyword, serp_data)
            if not result:
                self.checkpoint["failed"].append(keyword)
                self.stats["failed"] += 1
                return False

            # Parse and validate YAML
            try:
                yaml_content = strip_yaml_fences(result["content"])
                analysis_data = safe_yaml_load(yaml_content, keyword=keyword, logger=self.logger)

                if analysis_data is None:
                    log_json(self.logger, "yaml_parse_error", {
                        "keyword": keyword,
                        "error": "All parsing strategies failed - raw response saved for debugging"
                    })
                    self.checkpoint["failed"].append(keyword)
                    self.stats["failed"] += 1
                    # Continue to next keyword instead of raising exception
                    return False

                # Validate schema
                is_valid, errors = validate_yaml_schema(analysis_data)
                if not is_valid:
                    log_json(self.logger, "validation_errors", {
                        "keyword": keyword,
                        "errors": errors
                    })
                    # Continue with partial data instead of failing

                # Calculate quality score
                quality_score = calculate_quality_score(analysis_data)
                analysis_data["quality_score"] = quality_score

                # Quality gate check - warn but don't fail for low quality
                if quality_score < QUALITY_THRESHOLD:
                    log_json(self.logger, "quality_warning", {
                        "keyword": keyword,
                        "quality_score": quality_score,
                        "threshold": QUALITY_THRESHOLD,
                        "action": "saving_anyway"
                    })

                # Save output regardless of quality (user can filter later)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    yaml.dump(analysis_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

                self.checkpoint["completed"].append(keyword)
                self.stats["success"] += 1

                log_json(self.logger, "success", {
                    "keyword": keyword,
                    "quality_score": quality_score,
                    "tokens_used": result["usage"].get("total_tokens", 0)
                })

                return True

            except yaml.YAMLError as e:
                log_json(self.logger, "yaml_parse_error", {
                    "keyword": keyword,
                    "error": str(e)[:200]
                })
                self.checkpoint["failed"].append(keyword)
                self.stats["failed"] += 1
                return False
            except Exception as e:
                log_json(self.logger, "processing_error", {
                    "keyword": keyword,
                    "error": str(e)[:200]
                })
                self.checkpoint["failed"].append(keyword)
                self.stats["failed"] += 1
                return False

        except Exception as e:
            # Top-level catch-all to ensure the function never raises
            log_json(self.logger, "fatal_error", {
                "keyword": keyword,
                "error": str(e)[:200],
                "type": type(e).__name__
            })
            if keyword not in self.checkpoint["failed"]:
                self.checkpoint["failed"].append(keyword)
                self.stats["failed"] += 1
            return False

    async def run(self):
        """Run the analysis pipeline."""
        # Load keywords - scan from output directory or load from file
        if self.args.scan_output:
            keywords = scan_keywords_from_output_dir(OUTPUT_DIR)
            print(f"Scanned {len(keywords)} keywords from {OUTPUT_DIR}/")
            if not keywords:
                print(f"Error: No keyword directories found in {OUTPUT_DIR}/")
                print("  Expected structure: output/research/{keyword}/{keyword}-competitions.json")
                return
        else:
            keywords_path = Path(self.args.keywords_file)
            if not keywords_path.exists():
                print(f"Error: Keywords file not found: {self.args.keywords_file}")
                print("  Use --scan-output to scan from output directory instead")
                return
            keywords = load_keywords(self.args.keywords_file)

        self.stats["total"] = len(keywords)

        # Reset checkpoint if --force is set
        if self.args.force:
            self.checkpoint = {"completed": [], "failed": [], "last_index": 0}
            print("Force mode: ignoring checkpoint and overwriting existing outputs")
            log_json(self.logger, "force_mode", {"action": "checkpoint_reset"})

        # Resume from checkpoint if specified (ignored if --force)
        if self.args.resume_from and not self.args.force:
            try:
                start_index = int(self.args.resume_from)
                keywords = keywords[start_index:]
                log_json(self.logger, "resumed", {"from_index": start_index})
            except ValueError:
                pass

        log_json(self.logger, "started", {
            "total_keywords": len(keywords),
            "max_concurrency": self.args.max_concurrency,
            "model": MODEL,
            "dry_run": self.args.dry_run,
            "force": self.args.force,
            "source": "scan_output" if self.args.scan_output else "keywords_file"
        })

        timeout = ClientTimeout(total=self.args.timeout)
        async with ClientSession(timeout=timeout) as session:
            # Process in chunks for checkpointing
            for chunk_start in range(0, len(keywords), self.args.chunk_size):
                chunk_end = min(chunk_start + self.args.chunk_size, len(keywords))
                chunk = keywords[chunk_start:chunk_end]

                log_json(self.logger, "chunk_started", {
                    "chunk_start": chunk_start,
                    "chunk_end": chunk_end,
                    "chunk_size": len(chunk)
                })

                # Process chunk concurrently - return_exceptions prevents one failure from stopping others
                tasks = [self.analyze_keyword(session, kw) for kw in chunk]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Log any unexpected exceptions
                for kw, result in zip(chunk, results):
                    if isinstance(result, Exception):
                        log_json(self.logger, "unexpected_error", {
                            "keyword": kw,
                            "error": str(result)[:200],
                            "type": type(result).__name__
                        })
                        if kw not in self.checkpoint["failed"]:
                            self.checkpoint["failed"].append(kw)
                            self.stats["failed"] += 1

                # Save checkpoint after each chunk
                self.checkpoint["last_index"] = chunk_end
                save_checkpoint(self.checkpoint)

                log_json(self.logger, "chunk_completed", {
                    "chunk_end": chunk_end,
                    "success": self.stats["success"],
                    "failed": self.stats["failed"],
                    "skipped": self.stats["skipped"]
                })

        # Final summary
        log_json(self.logger, "completed", {
            "total": self.stats["total"],
            "success": self.stats["success"],
            "failed": self.stats["failed"],
            "skipped": self.stats["skipped"],
            "total_tokens": self.stats["total_tokens"]
        })

        print(f"\n{'='*50}")
        print("SERP Analysis Complete")
        print(f"{'='*50}")
        print(f"Total keywords: {self.stats['total']}")
        print(f"Success: {self.stats['success']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"Skipped: {self.stats['skipped']}")
        print(f"Total tokens used: {self.stats['total_tokens']}")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Phase 2.1: SERP Semantic Analysis using Grok-4 via OpenRouter"
    )

    parser.add_argument(
        "--keywords-file",
        default=KEYWORDS_FILE,
        help=f"Path to keywords file (default: {KEYWORDS_FILE})"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=CHUNK_SIZE,
        help=f"Keywords per checkpoint batch (default: {CHUNK_SIZE})"
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=MAX_CONCURRENCY,
        help=f"Parallel API calls (default: {MAX_CONCURRENCY})"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=TIMEOUT_SECONDS,
        help=f"HTTP timeout in seconds (default: {TIMEOUT_SECONDS})"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=MAX_TOKENS,
        help=f"Max output tokens (default: {MAX_TOKENS})"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=TEMPERATURE,
        help=f"LLM temperature (default: {TEMPERATURE})"
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Skip existing outputs"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Estimate cost without API calls"
    )
    parser.add_argument(
        "--resume-from",
        help="Resume from checkpoint index"
    )
    parser.add_argument(
        "--scan-output",
        action="store_true",
        help="Scan OUTPUT_DIR subdirectories for keywords instead of using keywords file"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore checkpoint file and overwrite existing outputs"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output for debugging"
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # Validate API key
    if OPENROUTER_API_KEY == "YOUR_API_KEY":
        print("Error: Please set OPENROUTER_API_KEY environment variable")
        print("  export OPENROUTER_API_KEY='your-api-key'")
        return

    analyzer = SERPAnalyzer(args)
    await analyzer.run()


if __name__ == "__main__":
    asyncio.run(main())
