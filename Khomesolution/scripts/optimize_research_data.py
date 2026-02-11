import os
import sys
import re
import json
import time
import argparse
from pathlib import Path

# Optional dependencies with graceful fallback
try:
    import tiktoken
    HAS_TIKTOKEN = True
except ImportError:
    HAS_TIKTOKEN = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# ==========================================
# CONFIGURATION
# ==========================================
BASE_SEARCH_PATH = "data/deep-research"
KEYWORDS_FILE = "data/keywords/keywords.txt"

PIPELINE_CONFIG = {
    "citation_optimization": True,
    "sentence_compression": True,
    "statistics_compression": True,
    "structure_optimization": True,
    "list_optimization": True,
    "redundancy_removal": True,
}

QUALITY_THRESHOLDS = {
    "max_heading_reduction": 0.60,
    "max_total_reduction": 0.70,
    "similarity_threshold": 0.65,
}

# ==========================================
# THAI LANGUAGE SUPPORT
# ==========================================
def contains_thai(text: str) -> bool:
    """Check if text contains Thai characters (U+0E00-U+0E7F)."""
    return bool(re.search(r'[\u0E00-\u0E7F]', text))

# ==========================================
# STAGE 0: Text Pre-processing
# ==========================================
def preprocess_text(text: str) -> str:
    """Join hard-wrapped lines, remove page numbers, and compress references.
    Research files from deep-research are often PDF-extracted with ~80 char
    line wrapping. This rejoins continuation lines so downstream stages
    (filler removal, list optimization, redundancy) work on complete text.
    """
    # Normalize smart quotes to ASCII (so regex filler patterns match)
    text = text.replace('\u2018', "'").replace('\u2019', "'")  # ' ' → '
    text = text.replace('\u201C', '"').replace('\u201D', '"')  # " " → "

    lines = text.split('\n')

    # Remove standalone page numbers (1-3 digit numbers alone on a line)
    lines = [l for l in lines if not re.match(r'^\s*\d{1,3}\s*$', l)]

    # --- Pass 1: Join hard-wrapped lines ---
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result.append('')
            continue

        # Join URL continuation fragments (no spaces, URL chars, prev line is URL)
        if (result and ' ' not in stripped and
            re.match(r'^https?://', result[-1], re.IGNORECASE) and
            re.search(r'[-/._~]', stripped)):
            result[-1] += stripped  # URL continuation — no space
            continue

        # Explicit block-start patterns
        is_block_start = bool(
            re.match(r'^[-*+•]\s', stripped) or          # bullet item
            re.match(r'^#{1,6}\s', stripped) or           # markdown heading
            re.match(r'^https?://', stripped, re.IGNORECASE) or  # URL on its own line
            re.match(r'^\d[\d\s,]*[A-Z]', stripped) or   # reference entry: "1 Title..."
            re.match(r'^\d+(?:\s+\d+){2,}', stripped) or   # multi-number ref: "2 4 6 21..."
            re.match(r'^\d+\s+[\u0E00-\u0E7F]', stripped)  # digit + Thai ref entry
        )

        # A non-block-start line is a continuation if it starts lowercase
        # or with a bracket/quote, OR if the previous line didn't end a sentence
        is_continuation = False
        # Find most recent non-blank line for context
        prev = ''
        prev_idx = len(result) - 1
        while prev_idx >= 0 and result[prev_idx] == '':
            prev_idx -= 1
        if prev_idx >= 0:
            prev = result[prev_idx]

        if not is_block_start and prev:
            # Never continue after a URL line (reference entries)
            if re.match(r'^https?://', prev, re.IGNORECASE):
                is_continuation = False
            elif stripped[0].islower() or stripped[0] in '()"\'–—,;':
                is_continuation = True
            elif not re.search(r'[.!?]\s*$', prev):
                # Previous line didn't end a sentence → likely continuation
                is_continuation = True

        if is_continuation:
            # Remove any blank lines between this and the previous content line
            while result and result[-1] == '':
                result.pop()
            if result:
                result[-1] += ' ' + stripped
            else:
                result.append(stripped)
        else:
            result.append(stripped)

    # --- Pass 2: Compress trailing reference section ---
    # Detect references: lines with "number(s) Title" followed by URL lines
    ref_start = None
    for i in range(len(result) - 1, max(len(result) // 2, 0), -1):
        line = result[i].strip()
        if not line:
            continue
        # Recognize: URLs, digit-prefixed entries (any language), URL fragments
        is_ref_line = bool(
            re.match(r'^https?://', line, re.IGNORECASE) or
            re.match(r'^\d[\d\s,]*[^\s\d,]', line) or  # digit(s) then any text
            (' ' not in line and re.search(r'[=&?/.]', line))  # URL fragment
        )
        if not is_ref_line:
            ref_start = i + 1
            break

    if ref_start is not None and ref_start < len(result):
        content_lines = result[:ref_start]
        ref_lines = result[ref_start:]

        # Extract just [numbers] URL pairs, drop verbose titles
        compressed_refs = []
        current_nums = None
        for line in ref_lines:
            line = line.strip()
            if not line:
                continue
            # URL line (may have trailing text from joined lines — strip it)
            url_match = re.match(r'^(https?://\S+)', line, re.IGNORECASE)
            if url_match:
                url = url_match.group(1)
                if current_nums is not None:
                    compressed_refs.append(f'[{current_nums}] {url}')
                else:
                    compressed_refs.append(url)
                current_nums = None
            else:
                # Title/number line — extract leading reference numbers
                nums_match = re.match(r'^([\d\s,]+)', line)
                if nums_match:
                    current_nums = ' '.join(nums_match.group(1).split())

        if compressed_refs:
            content_lines.append('')
            content_lines.append('## References')
            content_lines.extend(compressed_refs)
            result = content_lines

    # --- Pass 3: Strip inline bare reference numbers from body text ---
    # "...windows 1 2 ." → "...windows."
    # "...performance 16 17 ." → "...performance."
    text = '\n'.join(result)
    text = re.sub(r'\s+(\d{1,3}\s*)+(?=[.])', '', text)

    # Collapse runs of 3+ blank lines into 1
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

# ==========================================
# TOKEN COUNTING
# ==========================================
def count_tokens(text: str) -> int:
    if HAS_TIKTOKEN:
        enc = tiktoken.encoding_for_model("gpt-4")
        return len(enc.encode(text))
    # Fallback: ~4 characters per token
    return len(text) // 4

# ==========================================
# STAGE 1: Citation Optimization
# ==========================================
def optimize_citations(text: str) -> tuple:
    """
    - Deduplicate inline citations (max 2 per sentence)
    - Convert [text](url) -> numbered footnotes [n]
    - Remove [Strong]/[Moderate]/[Preliminary] labels
    - Return (optimized_text, references_list)
    """
    # Remove evidence quality labels: [Strong], [Moderate], [Preliminary]
    text = re.sub(r'\s*\[(Strong|Moderate|Preliminary)\]', '', text)
    # Also handle unbracketed prefix format: "• Strong:", "• Moderate:"
    text = re.sub(r'^(•\s*)(?:Strong|Moderate|Preliminary)\s*:\s*', r'\1', text, flags=re.MULTILINE)

    # Collect all markdown links and build reference list
    link_pattern = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
    references = []
    url_to_ref = {}

    def replace_link(match):
        url = match.group(2)
        base_url = url.split('#')[0] if '#:~:text=' in url else url
        if base_url not in url_to_ref:
            ref_num = len(references) + 1
            url_to_ref[base_url] = ref_num
            references.append(url)
        return f'[{url_to_ref[base_url]}]'

    text = link_pattern.sub(replace_link, text)

    # Deduplicate citations within sentences (max 2 per sentence)
    # Process per-line to preserve line structure (\n between bullets/paragraphs)
    processed_lines = []
    for line in text.split('\n'):
        sentences = re.split(r'(?<=[.!?])\s+', line)
        deduped_sentences = []
        for sentence in sentences:
            refs_in_sentence = re.findall(r'\[(\d+)\]', sentence)
            if len(refs_in_sentence) > 2:
                seen = []
                for ref in refs_in_sentence:
                    if ref not in seen:
                        seen.append(ref)
                keep_refs = set(seen[:2])
                count = {}
                def _remove_excess(m, _keep=keep_refs, _count=count):
                    ref = m.group(1)
                    if ref not in _keep:
                        return ''
                    _count[ref] = _count.get(ref, 0) + 1
                    if _count[ref] > 1:
                        return ''
                    return m.group(0)
                sentence = re.sub(r'\s*\[(\d+)\]', _remove_excess, sentence)
            deduped_sentences.append(sentence)
        processed_lines.append(' '.join(deduped_sentences))

    text = '\n'.join(processed_lines)
    text = re.sub(r'  +', ' ', text)
    return text, references

# ==========================================
# STAGE 2: Sentence Compression
# ==========================================
FILLER_PHRASES = [
    (r'\bIt is important to note that\s*', ''),
    (r'\bIt should be noted that\s*', ''),
    (r'\bIt is worth mentioning that\s*', ''),
    (r'\bin order to\b', 'to'),
    (r'\bdue to the fact that\b', 'because'),
    (r'\bas a matter of fact,?\s*', ''),
    (r'\bat the end of the day,?\s*', ''),
    (r'\bfor the purpose of\b', 'for'),
    (r'\bin the event that\b', 'if'),
    (r'\bwith regard to\b', 'regarding'),
    (r'\bwith respect to\b', 'regarding'),
    (r'\bin spite of the fact that\b', 'although'),
    (r'\bon the other hand,?\s*', ''),
    (r'\bFor instance,\s*', ''),
    (r'\bFor example,\s*', ''),
    (r'\bIn other words,\s*', ''),
    (r'\bessentially\s+', ''),
    (r'\bbasically\s+', ''),
    (r'\bfundamentally\s+', ''),
    (r'\bgenerally speaking,?\s*', ''),
    (r'\bIn practice,?\s*', ''),
    (r'\bIn essence,?\s*', ''),
    (r'\bIn fact,?\s*', ''),
    (r'\bAs a rule of thumb,?\s*', ''),
    (r'\bIt is worth noting that\s*', ''),
    (r'\bIt is also worth noting that\s*', ''),
    (r'\bIn general,?\s*', ''),
    (r'\bAs mentioned (?:above|earlier|before),?\s*', ''),
    (r'\bAs noted (?:above|earlier|before),?\s*', ''),
    (r"\bDon't forget to\s+", ''),
    (r'\bRemember,?\s+that\s+', ''),
    (r'\bRemember,\s*', ''),
    (r'\bKeep in mind that\s+', ''),
    (r'\bBe mindful that\s+', ''),
    (r'\bIt is also important to\s+', ''),
    (r'\bNote that\s+', ''),
    (r"\bIt'?s?\s+(?:also\s+)?worth noting that\s+", ''),
    (r"\bIt'?s?\s+wise to\s+", ''),
    (r"\bIt'?s?\s+recommended to\s+", ''),
    (r'\bAs a result,?\s*', ''),
    (r'\bIn particular,?\s*', ''),
    (r'\bIn addition,?\s*', ''),
    (r'\bMoreover,?\s*', ''),
    (r'\bFurthermore,?\s*', ''),
    (r'\bConsequently,?\s*', ''),
    (r'\bNonetheless,?\s*', ''),
    (r'\bNevertheless,?\s*', ''),
    (r'\bAdditionally,?\s*', ''),
    (r'\bConversely,?\s*', ''),
    (r'\bIn summary,?\s*', ''),
    (r'\bTo summarize,?\s*', ''),
    (r'\bAs a rule of thumb,?\s*', ''),
    (r'\bIn quantifiable terms,?\s*', ''),
    (r'\bAlways clarify\b', 'Clarify'),
    (r'\bThis (?:is|was) (?:a |the )?major consideration\s*', ''),
    (r'\bThis highlights\s+', ''),
    (r'\bIn some cases,?\s*', ''),
    (r'\bIn many cases,?\s*', ''),
    (r'\bWhile this is\b', 'This is'),
    (r'\bIt should be noted that\s+', ''),
    (r'\bIt can be noted that\s+', ''),
    (r'\bAdjust expectations accordingly:\s*', ''),
    (r'\bDrawbacks to be aware of:\s*', ''),
    (r'\bAnother issue can be\b', ''),
    (r'\bWhen budgeting,?\s*', ''),
    (r'\bMaintenance needs:\s*', ''),
    (r'\bEffect on daylight:\s*', ''),
    (r'\bCare and lifespan:\s*', ''),
    (r'\bKey price factors:\s*', ''),
    (r'\bVentilation impact:\s*', ''),
    (r'\bCommon post-installation issues:\s*', ''),
    (r'\bLimitations of DIY:\s*', ''),
    (r'\bSelection criteria:\s*', ''),
    (r'\bBottom line:\s*', ''),
    (r'\bFrame material cost differences:\s*', ''),
    (r'\bInstallation costs:\s*', ''),
    (r'\bAdditional expenses:\s*', ''),
    (r'\bComparing providers:\s*', ''),
    (r'\bValue vs\. Cost:\s*', ''),
    (r'\bHow much noise can they reduce\?\s*', ''),
    (r'\bSuitable home types:\s*', ''),
    (r'\bthe overall soundproofing of a room is only as strong as its weakest link –?\s*', ''),
    (r'\bThis tight sealing can\b', 'Can'),
    (r'\bwhile high-end aluminum or triple-pane systems may offer marginal gains at higher price\.?\s*', ''),
    (r'\bbut verify the performance specifications\.?\s*', ''),
    (r'\bwhich many homeowners and professionals consider well worth it\.?\s*', ''),
    (r'\bmost homeowners won\'t notice a difference in daylight\.?\s*', ''),
    (r'\bfor the purpose of\b', 'for'),
    (r'\b[Tt]aking care of soundproof windows is much like caring for any quality window\.?\s*', ''),
    (r'\bWith proper care, expect a long service life:\s*', ''),
    (r'\bAn improper install – even if the window itself is high-performance – may\b', 'An improper install may'),
    (r'\bHandling large, heavy glass safely requires at least two people and proper tools\.?\s*', ''),
    (r'\bThe install team also brings specialized equipment to safely hoist and anchor heavy acoustic units\.?\s*', ''),
    (r'\bBefore opting out of professional fitting\.?,?\s*', ''),
    (r'\bwhich, for many, justify the price\.?\s*', '.'),
    (r'\bPrices can vary by brand and supplier\.?\s*', ''),
    (r'\bOne might offer a basic double-glazed package at a lower cost, while another might include laminated glass or better frames for slightly more\.?\s*', ''),
    (r'\bHowever, with competitive shopping and possibly off-season discounts, you can find options that meet both your acoustic needs and budget\.?\s*', ''),
    (r'\bInstallation and any structural adjustments add to this\.?\s*', ''),
    (r'\bAlmost any home can install them, but\b', 'But'),
    (r'\bThey\'re also useful for home studios or nurseries where silence is golden\.?\s*', ''),
    (r'\bProfessional installation is recommended for full window replacements or when maximum acoustic performance is needed, to ensure the product delivers its rated noise reduction\.?\s*', ''),
    (r'\bProper acoustic caulking around the frame and wall interface ensures no flanking paths for sound\.?\s*', ''),
    (r'\bDIY is best for minor improvements and for those with carpentry experience\.?\s*', ''),
    (r'\bMany manufacturers rate their soundproof window systems for 20\+ years of performance before any major maintenance might be needed\.?\s*', ''),
    (r'\bRubber gaskets can lose elasticity over decades; wiping them and keeping them free of dirt will help longevity\.?\s*', ''),
    (r'\bUnless one opts for tinted acoustic glass or smaller window openings,?\s*', ''),
    # Thai filler phrases
    (r'เป็นที่น่าสังเกตว่า\s*', ''),           # It is worth noting that
    (r'สิ่งสำคัญที่ต้องทราบคือ\s*', ''),       # It is important to note that
    (r'ควรสังเกตว่า\s*', ''),                   # It should be noted that
    (r'เพื่อที่จะ', 'เพื่อ'),                   # in order to → to
    (r'เนื่องจากข้อเท็จจริงที่ว่า', 'เพราะ'),  # due to the fact that → because
    (r'เนื่องมาจากว่า', 'เพราะ'),               # owing to the fact that → because
    (r'โดยพื้นฐานแล้ว,?\s*', ''),               # basically/fundamentally
    (r'โดยหลักการแล้ว,?\s*', ''),               # in principle
    (r'กล่าวอีกนัยหนึ่ง,?\s*', ''),             # in other words
    (r'พูดอีกอย่างคือ,?\s*', ''),               # in other words (colloquial)
    (r'ยกตัวอย่างเช่น,?\s*', ''),               # for example
    (r'ตัวอย่างเช่น,?\s*', ''),                 # for instance
    (r'ในความเป็นจริง,?\s*', ''),               # as a matter of fact
    (r'ตามความเป็นจริงแล้ว,?\s*', ''),          # in reality
    (r'ในท้ายที่สุด,?\s*', ''),                 # at the end of the day
    (r'สรุปแล้ว,?\s*', ''),                     # in summary (filler usage)
    (r'โดยทั่วไปแล้ว,?\s*', ''),                # generally speaking
    (r'โดยทั่วๆ\s*ไป,?\s*', ''),               # generally (colloquial)
    (r'ในส่วนที่เกี่ยวกับ', 'เกี่ยวกับ'),       # with regard to → regarding
    (r'เกี่ยวเนื่องกับ', 'เกี่ยวกับ'),          # in connection with → regarding
    (r'ในทางกลับกัน,?\s*', ''),                 # on the other hand
    (r'อย่างไรก็ตาม,?\s*', ''),                 # however
    (r'อย่างไรก็ดี,?\s*', ''),                  # nevertheless
    (r'นอกจากนี้,?\s*', ''),                    # furthermore
    (r'ยิ่งไปกว่านั้น,?\s*', ''),               # moreover
    (r'ทั้งนี้,?\s*', ''),                      # in this regard
]

_ADJ_LIST = (
    r'important|effective|significant|good|large|small|high|low|fast|slow|'
    r'strong|weak|clear|hard|easy|useful|helpful|common|popular|powerful|successful'
)

REDUNDANT_MODIFIERS = [
    (rf'\bvery\s+({_ADJ_LIST})', r'\1'),
    (rf'\breally\s+({_ADJ_LIST})', r'\1'),
    (rf'\bquite\s+({_ADJ_LIST})', r'\1'),
    (rf'\bextremely\s+({_ADJ_LIST})', r'\1'),
    (rf'\bcompletely\s+({_ADJ_LIST})', r'\1'),
    (r'\btremendously\s+', ''),
    (r'\bcan potentially\b', 'can'),
    (r'\bmight potentially\b', 'might'),
    (r'\bcould potentially\b', 'could'),
    (r'\bnoticeably\s+', ''),
    (r'\bdramatically\s+', ''),
    (r'\bsignificantly\s+', ''),
    (r'\bsubstantially\s+', ''),
    # Thai redundant modifiers
    (r'อย่างมาก\s*', ''),                       # very much / significantly
    (r'ค่อนข้าง\s*', ''),                       # quite / rather
    (r'เป็นอย่างยิ่ง\s*', ''),                  # extremely
    (r'อย่างเห็นได้ชัด\s*', ''),                # obviously / clearly
]

def compress_sentences(text: str) -> str:
    for pattern, replacement in FILLER_PHRASES:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    for pattern, replacement in REDUNDANT_MODIFIERS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    # Fix capitalization after removals at sentence starts (skip URLs)
    text = re.sub(r'(?<=\.\s)([a-z])(?!ttps?://)', lambda m: m.group(1).upper(), text)
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'^ +', '', text, flags=re.MULTILINE)
    return text

# ==========================================
# STAGE 3: Statistics Compression
# ==========================================
STAT_PATTERNS = [
    (r'increased from\s+(\S+)\s+to\s+(\S+)', r'\1→\2'),
    (r'improved from\s+(\S+)\s+to\s+(\S+)', r'\1→\2'),
    (r'grew from\s+(\S+)\s+to\s+(\S+)', r'\1→\2'),
    (r'rose from\s+(\S+)\s+to\s+(\S+)', r'\1→\2'),
    (r'decreased from\s+(\S+)\s+to\s+(\S+)', r'\1→\2'),
    (r'dropped from\s+(\S+)\s+to\s+(\S+)', r'\1→\2'),
    (r'declined from\s+(\S+)\s+to\s+(\S+)', r'\1→\2'),
    (r'went from\s+(\S+)\s+to\s+(\S+)', r'\1→\2'),
    (r'changed from\s+(\S+)\s+to\s+(\S+)', r'\1→\2'),
    # Thai statistics patterns
    (r'เพิ่มขึ้นจาก\s*(\S+)\s*เป็น\s*(\S+)', r'\1→\2'),    # increased from X to Y
    (r'เพิ่มจาก\s*(\S+)\s*เป็น\s*(\S+)', r'\1→\2'),        # increased from X to Y (short)
    (r'ลดลงจาก\s*(\S+)\s*เป็น\s*(\S+)', r'\1→\2'),         # decreased from X to Y
    (r'ลดจาก\s*(\S+)\s*เป็น\s*(\S+)', r'\1→\2'),           # decreased from X to Y (short)
    (r'เปลี่ยนจาก\s*(\S+)\s*เป็น\s*(\S+)', r'\1→\2'),      # changed from X to Y
    (r'เติบโตจาก\s*(\S+)\s*เป็น\s*(\S+)', r'\1→\2'),       # grew from X to Y
    (r'สูงขึ้นจาก\s*(\S+)\s*เป็น\s*(\S+)', r'\1→\2'),      # rose from X to Y
    (r'ต่ำลงจาก\s*(\S+)\s*เป็น\s*(\S+)', r'\1→\2'),        # dropped from X to Y
    (r'ขยายจาก\s*(\S+)\s*เป็น\s*(\S+)', r'\1→\2'),         # expanded from X to Y
    (r'ปรับตัวจาก\s*(\S+)\s*เป็น\s*(\S+)', r'\1→\2'),      # adjusted from X to Y
]

def compress_parentheticals(text: str) -> str:
    """Remove parenthetical asides that are purely descriptive (no numbers/prices)."""
    def _should_remove(m):
        content = m.group(1)
        # Keep if it contains numbers, percentages, prices, or is very short
        if re.search(r'[\d%$฿]', content):
            return m.group(0)  # keep
        # Keep acronym definitions like "(PVB)", "(IGU)", "(STC)"
        if re.match(r'^[A-Z]{2,}$', content.strip()):
            return m.group(0)  # keep
        words = content.split()
        if len(words) <= 2:
            return m.group(0)  # keep short parentheticals
        return ''  # remove verbose descriptive parentheticals

    # Remove verbose parentheticals (>2 words, no numbers/acronyms)
    text = re.sub(r'\(([^)]{10,})\)', _should_remove, text)
    # Remove inline e.g./i.e. examples without numbers: "e.g. word word word"
    text = re.sub(r',?\s*e\.g\.\s+[^,.\d]{10,}?(?=[.,;])', '', text)
    text = re.sub(r',?\s*i\.e\.\s+[^,.\d]{10,}?(?=[.,;])', '', text)
    # Remove "such as X, Y, and Z" clauses without numbers
    text = re.sub(r',?\s*such as\s+[^,.\d]{10,}?(?=[.,;])', '', text)
    # Clean up artifacts: space before punctuation, double spaces
    text = re.sub(r'\s+([.,;:!?])', r'\1', text)
    text = re.sub(r'  +', ' ', text)
    return text

def remove_advisory_sentences(text: str) -> str:
    """Remove purely advisory/qualitative sentences that contain no data.
    Targets sentences that are opinion/advice without numbers, percentages,
    or technical specifications."""
    lines = text.split('\n')
    result = []
    for line in lines:
        if not line.strip() or line.strip().startswith('#') or line.strip().startswith('['):
            result.append(line)
            continue

        # Split line into sentences
        sentences = re.split(r'(?<=[.!?])\s+', line)
        kept = []
        for sent in sentences:
            # Keep sentences with quantitative data
            has_data = bool(re.search(r'[\d%$฿]|STC|dB|mm\b|m²', sent))
            # Keep short sentences (likely important)
            if has_data or len(sent) < 60:
                kept.append(sent)
                continue
            # Remove sentences that are purely advisory
            is_advisory = bool(re.match(
                r'^\s*(Consider|Ensure|Avoid|Watch for|Adjust|Prepare to|'
                r'Homeowners should|This (?:robust|professional|tight)|'
                r'These factors can|This can be|'
                r'If (?:on a tight budget|total window)|'
                r'When (?:comparing|budgeting|seals))',
                sent
            ))
            if is_advisory:
                continue  # skip this sentence
            kept.append(sent)

        result.append(' '.join(kept))
    return '\n'.join(result)

def compress_statistics(text: str) -> str:
    for pattern, replacement in STAT_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

# ==========================================
# STAGE 4: Structure Optimization (DISABLED)
# ==========================================
def optimize_structure(text: str) -> str:
    """Inline short H3 sections as bold text."""
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('### '):
            heading_text = line[4:].strip()
            content_lines = []
            j = i + 1
            while j < len(lines) and not lines[j].startswith('#'):
                if lines[j].strip():
                    content_lines.append(lines[j].strip())
                j += 1
            if len(content_lines) <= 3:
                combined = f"**{heading_text}**: {' '.join(content_lines)}"
                result.append(combined)
                result.append('')
                i = j
                continue
        result.append(line)
        i += 1
    return '\n'.join(result)

# ==========================================
# STAGE 5: List Optimization
# ==========================================
def optimize_lists(text: str) -> str:
    """Convert small bullet lists (<=4 items) into flowing paragraph text."""
    lines = text.split('\n')
    result = []
    i = 0
    while i < len(lines):
        if re.match(r'^[-*+•]\s+', lines[i]):
            list_items = []
            j = i
            while j < len(lines) and re.match(r'^[-*+•]\s+', lines[j]):
                item = re.sub(r'^[-*+•]\s+', '', lines[j]).strip()
                list_items.append(item)
                j += 1

            if len(list_items) <= 6:
                # Lowercase subsequent items for flow (skip if starts with uppercase acronym/proper noun pattern)
                processed = [list_items[0]]
                for item in list_items[1:]:
                    if item and item[0].isupper() and (len(item) < 2 or item[1].islower()):
                        processed.append(item[0].lower() + item[1:])
                    else:
                        processed.append(item)

                if len(processed) == 1:
                    paragraph = processed[0]
                elif len(processed) == 2:
                    paragraph = f"{processed[0]}; and {processed[1]}"
                else:
                    parts = '; '.join(processed[:-1])
                    paragraph = f"{parts}, and {processed[-1]}"

                paragraph = paragraph.rstrip('.')
                paragraph += '.'
                result.append(paragraph)
                i = j
            else:
                # Keep all items as-is (list too large to merge)
                for k in range(i, j):
                    result.append(lines[k])
                i = j
        else:
            result.append(lines[i])
            i += 1
    return '\n'.join(result)

# ==========================================
# STAGE 6: Redundancy Removal
# ==========================================
def _char_trigrams(text: str) -> set:
    """Generate character trigrams for Thai text similarity."""
    text = re.sub(r'\s+', '', text)
    return set(text[i:i+3] for i in range(len(text) - 2)) if len(text) >= 3 else {text}

def word_overlap_similarity(text1: str, text2: str) -> float:
    """Fallback similarity using word overlap (Jaccard).
    Uses character trigrams for Thai text since Thai lacks word boundaries."""
    if contains_thai(text1) or contains_thai(text2):
        set1 = _char_trigrams(text1)
        set2 = _char_trigrams(text2)
    else:
        set1 = set(re.findall(r'\w+', text1.lower()))
        set2 = set(re.findall(r'\w+', text2.lower()))
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)

def compute_similarity(text1: str, text2: str) -> float:
    if HAS_SKLEARN:
        try:
            # Use character n-grams for Thai (no word boundaries); word-level for English
            if contains_thai(text1) or contains_thai(text2):
                vectorizer = TfidfVectorizer(analyzer='char_wb', ngram_range=(2, 4))
            else:
                vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([text1, text2])
            return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except Exception:
            pass
    return word_overlap_similarity(text1, text2)

def remove_redundancy(text: str, threshold: float = 0.85) -> str:
    """Remove lines/paragraphs with >threshold similarity to an earlier one."""
    # Split into logical blocks: each line that contains substantial text
    lines = text.split('\n')
    kept = []
    kept_texts = []  # stripped text of kept lines for comparison

    for line in lines:
        stripped = line.strip()

        # Always keep: empty lines, headings, short lines, reference lines
        if (not stripped or stripped.startswith('#') or len(stripped) < 80 or
                stripped.startswith('[') or stripped.startswith('http')):
            kept.append(line)
            continue

        # Check against kept substantial lines
        is_redundant = False
        for kt in kept_texts:
            if compute_similarity(stripped, kt) > threshold:
                is_redundant = True
                break

        if not is_redundant:
            kept.append(line)
            kept_texts.append(stripped)
        # else: skip this redundant line

    return '\n'.join(kept)

# ==========================================
# QUALITY VALIDATION
# ==========================================
def extract_numbers(text: str) -> set:
    numbers = set()
    numbers.update(re.findall(r'\d+(?:\.\d+)?%', text))
    numbers.update(re.findall(r'\$[\d,]+(?:\.\d+)?', text))
    numbers.update(re.findall(r'\b\d+(?:\.\d+)?[xX]\b', text))
    return numbers

def extract_headings(text: str) -> list:
    return re.findall(r'^#{1,6}\s+.+', text, re.MULTILINE)

def validate_quality(original: str, optimized: str) -> tuple:
    issues = []

    # Check percentages / costs preserved
    orig_numbers = extract_numbers(original)
    opt_numbers = extract_numbers(optimized)
    missing = orig_numbers - opt_numbers
    # Numbers may appear inside arrow notation
    missing = {n for n in missing if n not in optimized}
    if missing:
        issues.append(f"Missing numbers/percentages: {missing}")

    # Check headings not over-reduced
    orig_h = extract_headings(original)
    opt_h = extract_headings(optimized)
    if orig_h:
        ratio = 1 - (len(opt_h) / len(orig_h))
        if ratio > QUALITY_THRESHOLDS["max_heading_reduction"]:
            issues.append(
                f"Too many headings removed: {ratio:.0%} "
                f"(max {QUALITY_THRESHOLDS['max_heading_reduction']:.0%})"
            )

    # Check total reduction
    orig_t = count_tokens(original)
    opt_t = count_tokens(optimized)
    if orig_t > 0:
        reduction = 1 - (opt_t / orig_t)
        if reduction > QUALITY_THRESHOLDS["max_total_reduction"]:
            issues.append(
                f"Total reduction too aggressive: {reduction:.0%} "
                f"(max {QUALITY_THRESHOLDS['max_total_reduction']:.0%})"
            )

    return len(issues) == 0, issues

# ==========================================
# MAIN OPTIMIZATION PIPELINE
# ==========================================
def optimize_markdown(text: str, config: dict = None, debug: bool = False) -> tuple:
    if config is None:
        config = PIPELINE_CONFIG

    report = {"original_tokens": count_tokens(text), "stages": []}
    references = []

    def _dbg(stage_name):
        if debug:
            t = count_tokens(text)
            saved = report["original_tokens"] - t
            pct = saved / report["original_tokens"] * 100 if report["original_tokens"] else 0
            print(f"  [{stage_name}] {t:,} tokens (saved {saved:,}, {pct:.1f}%)")

    # Stage 0: Pre-processing (join hard-wrapped lines, remove page numbers)
    text = preprocess_text(text)
    report["stages"].append("preprocess")
    _dbg("preprocess")

    # Stage 1
    if config.get("citation_optimization", True):
        text, references = optimize_citations(text)
        report["stages"].append("citation_optimization")
        _dbg("citations")

    # Stage 2
    if config.get("sentence_compression", True):
        text = compress_sentences(text)
        report["stages"].append("sentence_compression")
        _dbg("sentences")

    # Stage 2b: Parenthetical compression
    text = compress_parentheticals(text)
    _dbg("parentheticals")

    # Stage 2c: Remove advisory sentences
    text = remove_advisory_sentences(text)
    _dbg("advisory")

    # Stage 3
    if config.get("statistics_compression", True):
        text = compress_statistics(text)
        report["stages"].append("statistics_compression")
        _dbg("statistics")

    # Stage 4
    if config.get("structure_optimization", True):
        text = optimize_structure(text)
        report["stages"].append("structure_optimization")
        _dbg("structure")

    # Stage 5
    if config.get("list_optimization", True):
        text = optimize_lists(text)
        report["stages"].append("list_optimization")
        _dbg("lists")

    # Stage 6
    if config.get("redundancy_removal", True):
        text = remove_redundancy(text, QUALITY_THRESHOLDS["similarity_threshold"])
        report["stages"].append("redundancy_removal")
        _dbg("redundancy")

    # Append numbered references
    if references:
        text = text.rstrip('\n') + '\n\n## Numbered Citations\n\n'
        for i, url in enumerate(references, 1):
            text += f'[{i}] {url}\n'

    report["optimized_tokens"] = count_tokens(text)
    report["reduction"] = (
        1 - (report["optimized_tokens"] / report["original_tokens"])
        if report["original_tokens"] > 0
        else 0
    )
    return text, report

# ==========================================
# FILE PROCESSING
# ==========================================
def get_keywords(filepath: str) -> list:
    if not Path(filepath).exists():
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return [l.strip() for l in f if l.strip() and not l.startswith('#')]

def process_file(research_file: Path, base_dir: Path, force: bool = False) -> dict:
    stem = research_file.stem
    output_file = base_dir / f"{stem}.optimized.md"

    if output_file.exists() and not force:
        print(f"\u251c\u2500\u2500 Skipping {research_file.name}: already optimized.")
        return None

    print(f"\u251c\u2500\u2500 Processing {research_file.name}")

    original_text = research_file.read_text(encoding='utf-8')
    optimized_text, report = optimize_markdown(original_text)
    report["file"] = research_file.name

    # Quality validation
    passed, issues = validate_quality(original_text, optimized_text)
    report["quality_passed"] = passed
    report["quality_issues"] = issues

    if not passed:
        print(f"\u2502   \u251c\u2500\u2500 Quality FAILED:")
        for issue in issues:
            print(f"\u2502   \u2502   - {issue}")
        print(f"\u2502   \u2514\u2500\u2500 Reverted to original")
        optimized_text = original_text
        report["reverted"] = True
    else:
        report["reverted"] = False

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(optimized_text, encoding='utf-8')

    orig_t = report['original_tokens']
    opt_t = report['optimized_tokens']
    reduction = report['reduction']
    print(f"\u2502   \u251c\u2500\u2500 Before: {orig_t:,} tokens")
    print(f"\u2502   \u251c\u2500\u2500 After:  {opt_t:,} tokens")
    print(f"\u2502   \u2514\u2500\u2500 Saved:  {reduction:.1%}")
    return report

# ==========================================
# MAIN
# ==========================================
if __name__ == "__main__":
    # Ensure UTF-8 output on Windows (avoids cp874 encoding errors for tree characters)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(
        description="Markdown Token Optimizer - Reduce token count by 45-55%"
    )
    parser.add_argument("--keywords", default=KEYWORDS_FILE, help="Path to keywords file")
    parser.add_argument("--dir", default=BASE_SEARCH_PATH, help="Base directory to scan")
    parser.add_argument("--all", action="store_true", help="Scan directory for all research .md files")
    parser.add_argument("--force", action="store_true", help="Re-process even if optimized file exists")
    parser.add_argument("--keyword", type=str, help="Process a single keyword instead of the full list")

    args = parser.parse_args()
    base_dir = Path(args.dir)

    start_time = time.time()

    # Determine which files to process
    if args.all:
        # Scan directory for all *-research.md files (exclude .optimized.md)
        md_files = sorted(
            f for f in base_dir.glob("*-research.md")
            if ".optimized." not in f.name
        )
    elif args.keyword:
        md_files = [base_dir / f"{args.keyword}-research.md"]
    else:
        keywords = get_keywords(args.keywords)
        md_files = [base_dir / f"{kw}-research.md" for kw in keywords]

    if not md_files:
        print("No research files found.")
        exit(1)

    print(f"\u251c\u2500\u2500 Scanning {base_dir}/*.md")
    print(f"\u251c\u2500\u2500 Found {len(md_files)} research documents")

    results = []
    for md_file in md_files:
        if not md_file.exists():
            print(f"\u251c\u2500\u2500 Skipping {md_file.name}: file not found")
            continue
        report = process_file(md_file, base_dir, force=args.force)
        if report:
            results.append(report)

    elapsed = time.time() - start_time

    # Batch summary
    if results:
        total_orig = sum(r["original_tokens"] for r in results)
        total_opt = sum(r["optimized_tokens"] for r in results)
        total_saved = total_orig - total_opt
        total_reduction = 1 - (total_opt / total_orig) if total_orig > 0 else 0
        reverted = sum(1 for r in results if r.get("reverted", False))

        print(f"\u2502")
        print(f"\u2514\u2500\u2500 Complete! Total saved: {total_saved:,} tokens ({total_reduction:.1%})")

        # Save JSON report
        report_data = {
            "total_files_processed": len(results),
            "total_tokens_before": total_orig,
            "total_tokens_after": total_opt,
            "total_reduction": f"{total_reduction:.1%}",
            "processing_time": f"{elapsed:.1f}s",
            "quality_reverts": reverted,
            "files": [
                {
                    "file": r.get("file", ""),
                    "tokens_before": r["original_tokens"],
                    "tokens_after": r["optimized_tokens"],
                    "reduction": f"{r['reduction']:.1%}",
                    "quality_passed": r.get("quality_passed", True),
                    "reverted": r.get("reverted", False),
                }
                for r in results
            ],
        }
        report_path = base_dir / "_optimization_report.json"
        report_path.write_text(
            json.dumps(report_data, indent=2, ensure_ascii=False), encoding='utf-8'
        )
        print(f"\nReport saved: {report_path}")
    else:
        print(f"\u2502")
        print(f"\u2514\u2500\u2500 No files were processed.")
