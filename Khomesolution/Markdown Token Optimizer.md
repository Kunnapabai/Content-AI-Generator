# Markdown Token Optimizer — Script Workflow Explanation

## What It Does

`markdown_optimizer.py` is a **pure algorithmic** (no LLM calls) tool that reduces markdown token count by **45-55%** while preserving critical information like statistics, citations, and structure.

---

## Workflow When Running `uv run scripts/markdown_optimizer.py --all`

```
┌─────────────────────────────────────────────────────────┐
│  1. READ keywords.txt                                   │
│     data/keywords/keywords.txt                          │
│     → Loads all keyword lines (skips comments/#)        │
└──────────────────────┬──────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│  2. FOR EACH KEYWORD, find research file:               │
│     output/research/{keyword}/{keyword}-research.md     │
└──────────────────────┬──────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│  3. RUN 6-STAGE OPTIMIZATION PIPELINE                   │
│                                                         │
│  Stage 1: Citation Optimization                         │
│    • Deduplicate inline citations (max 2 per sentence)  │
│    • Convert [text](url) → numbered footnotes [1]       │
│    • Remove [Strong]/[Moderate]/[Preliminary] labels    │
│    • Append numbered reference list at bottom           │
│                                                         │
│  Stage 2: Sentence Compression                          │
│    • Remove filler phrases ("in order to" → "to")       │
│    • Remove redundant modifiers ("very important"       │
│      → "important")                                     │
│    • Compress example introductions                     │
│                                                         │
│  Stage 3: Statistics Compression                        │
│    • "increased from 50% to 90%" → "50%→90%"           │
│                                                         │
│  Stage 4: Structure Optimization (DISABLED by default)  │
│    • Would inline short H3 sections as bold text        │
│                                                         │
│  Stage 5: List Optimization                             │
│    • Convert small bullet lists (≤4 items) into         │
│      flowing paragraph text                             │
│                                                         │
│  Stage 6: Redundancy Removal                            │
│    • TF-IDF cosine similarity (or word-overlap fallback)│
│    • Remove paragraphs with >85% similarity             │
└──────────────────────┬──────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│  4. QUALITY VALIDATION                                  │
│    • Check all percentages, costs, model names preserved│
│    • Ensure headings not over-reduced (max 60% removed) │
│    • Ensure total reduction ≤ 70%                       │
│    • If quality check FAILS → return original unchanged │
└──────────────────────┬──────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│  5. SAVE OUTPUT                                         │
│     output/research/{keyword}/{keyword}-research-       │
│     optimized.md                                        │
│     + Print optimization report per file                │
│     + Print batch summary at end                        │
└─────────────────────────────────────────────────────────┘
```

---

## Before & After Example (Dragon Ball Z Sample)

### BEFORE (Original Research Markdown)
```markdown
## Goku's Power Levels

It is important to note that Goku's power level increased from
334 to 8000 during the Saiyan Saga
[Dragon Ball Wiki](https://dragonball.fandom.com/wiki/Goku)
[Power Level Guide](https://dbz-power.com/goku#:~:text=saiyan+saga+power).
This was essentially a very important transformation [Strong].

### Training Methods

Goku used the following techniques:
- Gravity training at 100x Earth's gravity
- Sparring with Vegeta
- Learning the Kaioken technique

For instance, in the Hyperbolic Time Chamber, Goku basically
trained for a full year in order to master Super Saiyan 2
[Training Source](https://dbz-training.com/chamber).

### Combat Techniques

In other words, Goku's combat techniques are quite effective
due to the fact that he trained under multiple masters
[Master Roshi](https://dragonball.fandom.com/wiki/Roshi)
[King Kai](https://dragonball.fandom.com/wiki/KingKai)
[Whis](https://dragonball.fandom.com/wiki/Whis).

Goku's power level improved from 8000% to 150000000%, which
was a completely significant milestone. Goku's combat
abilities were really good and very effective against Frieza.

Goku's fighting skills improved tremendously under many
teachers and his combat capabilities were extremely effective
against the tyrant Frieza in their legendary battle.
```

### AFTER (Optimized)
```markdown
## Goku's Power Levels

Goku's power level 334→8000 during the Saiyan Saga [1].
This was a important transformation.

### Training Methods

Gravity training at 100x Earth's gravity; sparring with Vegeta,
and learning the Kaioken technique.

Hyperbolic Time Chamber, Goku trained for a full year to master
Super Saiyan 2 [2].

### Combat Techniques

Goku's combat techniques are effective because he trained under
multiple masters [3] [4].

Goku's power level 8000%→150000000%, which was a significant
milestone. Goku's combat abilities were effective against Frieza.

## Numbered Citations

[1] https://dragonball.fandom.com/wiki/Goku
[2] https://dbz-training.com/chamber
[3] https://dragonball.fandom.com/wiki/Roshi
[4] https://dragonball.fandom.com/wiki/KingKai
```

### What Changed

| Stage | What Happened |
|---|---|
| **Citations** | `[Dragon Ball Wiki](url)` → `[1]`, duplicates removed (max 2/sentence), `[Strong]` label removed |
| **Sentences** | "It is important to note that" → removed, "essentially" → removed, "in order to" → "to", "due to the fact that" → "because" |
| **Statistics** | "increased from 334 to 8000" → "334→8000" |
| **Lists** | 3 bullet points → flowing paragraph with semicolons |
| **Modifiers** | "very important" → "important", "really good" → "good", "quite effective" → "effective" |
| **Redundancy** | Second paragraph about Frieza (85%+ similarity) → removed |

---

## Benefits

- **45-55% token reduction** — Cuts LLM input costs roughly in half when feeding research docs to downstream article generation
- **Zero LLM calls** — Pure regex/algorithmic processing, so it's fast and free (no API costs)
- **Quality-safe** — Built-in validator ensures critical data (percentages, costs, model names, source counts) is never lost; auto-reverts to original if too much is removed
- **Citation traceability preserved** — Full URLs with text fragments kept in numbered references at the bottom, so sources remain verifiable
- **Batch processing** — `--all` flag processes every keyword in `keywords.txt` in one run, with per-file reports and a batch summary
- **Idempotent output** — Creates a separate `-optimized.md` file, never overwrites the original research document
- **Configurable pipeline** — Each optimization stage can be toggled on/off via config dict (e.g., structure optimization is disabled by default due to known bugs)
- **Graceful degradation** — Falls back to character-based estimation if `tiktoken` isn't installed, and word-overlap detection if `scikit-learn` isn't available
