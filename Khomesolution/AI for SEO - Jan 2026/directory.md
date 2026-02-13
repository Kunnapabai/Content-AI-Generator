# SuperBank Directory Structure

## .claude/
> **Claude Code command registry for the content pipeline.** Contains sequential automation phases (1.x-9.x): data collection, title analysis, outline creation, deep research, article generation, SEO metadata, image creation, and WordPress publishing.

```
.claude
├── commands
│   ├── 1.1-data-collection.md      # SERP data collection via DataForSEO
│   ├── 1.2-data-collection.md      # Flikover/Serper keyword export
│   ├── 1.3-autocomplete.md         # Google Autocomplete expansion
│   ├── 1.4-autocomplete.md         # Merge Ahrefs + Autocomplete CSV
│   ├── 2.1-title-analysis.md       # Grok-powered SERP title analysis
│   ├── 3.1-outline-creation.md     # Batch outline generation
│   ├── 4-deep-research-requirement.md   # Generate research prompts
│   ├── 4.1-deep-research-processing.md  # ChatGPT Selenium automation
│   ├── 5.1-deep-research-merge-data.md  # Markdown token optimizer
│   ├── 6-post-plan-processing.md   # AI article generation with citations
│   ├── 7.0-meta-seo.md             # Parallel SEO generation
│   ├── 7.1-first-sentence.md       # Generate first sentences
│   ├── 7.2-meta-description.md     # Generate meta descriptions
│   ├── 8.0-feature-image-prompt.md # Feature image prompt generation
│   ├── 8.1-create-feature-image.md # Generate feature images
│   ├── 8.2-infographic-prompt.md   # Infographic prompt generation
│   ├── 8.3-create-infographic.md   # Generate infographics
│   ├── 8.4-resize-remove-exif-image.md  # Image optimization
│   ├── 9.-pick-author.md           # WordPress auto-post
│   └── spec-builder.md             # Iterative spec discovery
├── settings.json
└── settings.local.json
```


## data/
> **Central data repository for the SEO pipeline.** Stores keyword lists, target URLs, and processed exports organized by keyword campaigns. Supports multi-keyword tracking with session logs.

```
data
├── downloads                       # Downloaded content storage
├── exports                         # Processed data exports by keyword
│   ├── หลังคาใส
│   │   ├── all_urls/*.csv
│   │   └── หลังคาใส.csv
│   ├── กระจกกันเสียง
│   │   ├── all_urls/*.csv
│   │   └── กระจกกันเสียง.csv
│   └── หลังคาโปร่งแสง
│       ├── all_urls/*.csv
│       └── หลังคาโปร่งแสง.csv
├── keywords
│   └── keywords.txt                # Source keyword lists
└── urls
    ├── หลังคาใส_urls.json
    ├── กระจกกันเสียง_urls.json
    └── หลังคาโปร่งแสง_urls.json
```


## logs/
> **Application and publishing logs.** Tracks AI content generation processes (deepresearch, outline, meta) and WordPress auto-posting activities with timestamps.

```
logs
├── deepresearch_generator.log
├── first_sentence_generator.log
├── meta_description_generator.log
├── outline_master_generator.log
├── wp_auto_posts.*.jsonl           # WordPress posting logs
└── wp_auto_summary.*.json          # Posting summary reports
```


## secrets/
> **Credentials and API keys.** Contains sensitive configuration for Google Cloud, API authentication, and environment variables.

```
secrets
├── credentials.json
├── .env
└── google-cloud-credentials.json
```


## specs/
> **Prompt specifications and templates.** Defines task workflows for AI content generation with input/output paths, processing rules, and quality criteria.

```
specs
├── auto_post_prompt.md             # WordPress posting prompt
├── deepresearch-script.md          # Deep research execution
├── deepresearch.md                 # Research specifications
├── featureimg/doctor/1.png         # Sample feature images
├── first_sentence-script.yaml      # First sentence generation
├── first_sentence.yaml
├── follow-up-deepresearch.md
├── meta_description-script.yaml    # Meta description generation
├── meta_description.yaml
├── outline                         # Outline specifications
│   ├── outline-master.md
│   ├── title-analysis.md
│   └── title-generate.md
├── outline-analysis-script.md
├── outline-analysis.md
├── outline-script.md
├── outline.md
├── prompt_guide.md                 # Prompt writing guidelines
├── schema-generator.yaml
├── semantic-outline.yaml
├── title-analysis-script.md
├── title-analysis.md
├── title-generator-script.md
└── title-generator.md
```


## scripts/
> **Standalone automation scripts.** Handles keyword expansion (DataForSEO), deep research (ChatGPT Selenium), AI image generation (OpenRouter/Replicate), content optimization, GSC reports, and WordPress publishing.

```
scripts
├── autocomplete_dataforseo.py      # Keyword expansion via DataForSEO
├── backup_deepresearch.py
├── create-feature-img-openrouter.py    # Feature image generation
├── create-feature-img-replicate.py
├── create-infographic-img-openrouter.py
├── create-infographic-img-replicate.py
├── debug_click.py                  # Debugging utilities
├── debug_page_state.py
├── debug_selectors.py
├── deepresearch_gpt.py             # ChatGPT Selenium automation
├── deepresearch_llm.py
├── execute_outline_generation.py
├── execute_task_3.py
├── gsc_ctr_report.py               # Google Search Console reports
├── image-gdrive.py                 # Google Drive image download
├── keywords_collections.py
├── meta_description_generator.py
├── outline_analysis_llm.py
├── outline_llm.py
├── outline_master.py
├── outline_optimize.py
├── re-size-image.py                # Image resizing/EXIF removal
├── start-chrome-debug.sh           # Chrome debug mode
├── test_wp_access.py
├── title_analysis_llm.py
├── title_generator_llm.py
└── wp_auto_post.py                 # WordPress auto-publishing
```


## src/bankcontent/
> **Main Python package for the content pipeline.** Structured around specialized modules: `core` (LLM client, circuit breaker), `collectors` (Flikover/SERP data), `analyzers` (SERP analysis), `outline` (article outlines), `deepresearch` (research specs), `postplan` (article planning), `meta_seo` (SEO elements), and `services` (GSC, GSheet, Serper APIs).

```
src/bankcontent
├── __init__.py
├── analytics/                      # Budget & usage tracking
│   ├── budget_tracker.py
│   └── usage_tracker.py
├── analyzers/                      # SERP analysis
│   └── serp_analyzer.py
├── cli/                            # Command-line interface
│   └── main.py
├── collectors/                     # Data collection modules
│   ├── flikover/                   # Flikover integration
│   │   ├── csv_merger.py
│   │   ├── exporter.py
│   │   ├── orchestrator.py
│   │   ├── session_reporter.py
│   │   ├── url_builder.py
│   │   └── url_processor.py
│   └── serp/                       # SERP data collection
├── config/                         # Settings & configuration
│   ├── logger.py
│   ├── models.py
│   ├── schemas/title-analysis-schema.json
│   └── settings.py
├── core/                           # Core utilities
│   ├── circuit_breaker.py          # API resilience
│   ├── exceptions.py
│   ├── llm_client.py               # LLM API wrapper
│   ├── usage.py
│   └── utils.py
├── deepresearch/                   # Deep research runner
│   └── runner.py
├── gsc_reports/                    # Google Search Console
│   ├── analyzer.py
│   ├── exporter.py
│   ├── fetcher.py
│   └── generator.py
├── managers/                       # Resource managers
│   ├── chrome_manager.py           # Browser automation
│   └── keyword_manager.py
├── meta_seo/                       # SEO content generation
│   ├── first_sentence.py
│   └── meta_description.py
├── outline/                        # Outline generation
│   ├── analysis_runner.py
│   ├── runner.py
│   └── runner_master.py
├── postplan/                       # Article planning pipeline
│   ├── main.py
│   ├── pipeline/
│   │   ├── 04_questions.py
│   │   ├── 05_answers.py
│   │   └── 06_wordpress.py
│   └── templates/
│       ├── answer.md
│       └── answer.yml
├── services/                       # External API integrations
│   ├── gsc/                        # Google Search Console
│   │   ├── client.py
│   │   └── models.py
│   ├── gsheet/                     # Google Sheets
│   │   └── client.py
│   └── serper/                     # Serper API
│       └── client.py
├── title_analysis/                 # Title generation & analysis
│   ├── openrouter.py
│   ├── prompt_cache.py
│   ├── runner.py
│   ├── title_generator.py
│   └── validator.py
└── utils/                          # Helper utilities
    ├── report_generator.py
    ├── webhook.py
    └── ws_events.py
```


---

## Commands Reference

> **Detailed command specifications for each pipeline phase.** Each command runs with `model: haiku` and includes allowed tools, execution commands, and purpose descriptions.

### Phase 1: Data Collection

> **1.1-data-collection.md** - SERP Data Collection via DataForSEO

```
Tools:    Bash, Read, TodoWrite
Command:  uv run -m bankcontent.managers.keyword_manager
Purpose:  Collects Google SERP data including organic results, related keywords,
          and People Also Ask (PAA) questions using the DataForSEO API.
```

> **1.2-data-collection.md** - Flikover/Serper Keyword Export & CSV Merge

```
Tools:    Bash, Read, TodoWrite
Command:  uv run bankcontent --country th --num 30 --top-urls 3 --hl th --merge
Purpose:  Exports keyword data from Flikover/Serper APIs and merges into
          consolidated CSV files for Thai (TH) market targeting.
Params:   --country th    Target country
          --num 30        Number of results
          --top-urls 3    Top URLs to extract
          --hl th         Language setting
          --merge         Merge output files
```

> **1.3-autocomplete.md** - Google Autocomplete Keyword Expansion

```
Tools:    Bash, Read, TodoWrite
Command:  uv run python scripts/autocomplete_dataforseo.py --api-method standard --yes
Optional: uv run python scripts/autocomplete_dataforseo.py --api-method live --yes
Purpose:  Expands seed keywords using Google Autocomplete suggestions via DataForSEO API.
```

> **1.4-autocomplete.md** - Merge Ahrefs + Autocomplete into Master Query CSV

```
Tools:    Bash, Read, TodoWrite
Command:  uv run python scripts/kw-semantic/step1_merge.py --all
Purpose:  Consolidates Ahrefs keyword data with autocomplete suggestions into
          a unified master query CSV for downstream processing.
```

### Phase 2: Title Analysis

> **2.1-title-analysis.md** - Grok-Powered SERP Title Analysis

```
Tools:    Bash, Read, TodoWrite
Command:  uv run scripts/title_analysis_llm.py
Purpose:  Analyzes SERP titles using Grok LLM via OpenRouter to identify patterns,
          extract insights, and inform title generation strategy.
Ref:      specs/outline/title-analysis.md (optional)
```

### Phase 3: Outline Creation

> **3.1-outline-creation.md** - Batch Outline Generation

```
Tools:    Bash, Read, TodoWrite
Command:  uv run scripts/outline_master.py
Purpose:  Generates article outlines in batch using outline-master.md prompt template.
          Creates structured content blueprints for each keyword.
```

### Phase 4: Deep Research

> **4-deep-research-requirement.md** - Generate Deep Research Prompts

```
Tools:    Bash, Read, TodoWrite
Command:  uv run scripts/deepresearch_llm.py
Purpose:  Transforms article outlines into deep research prompts using Grok LLM.
          Generates research specifications for comprehensive content gathering.
```

> **4.1-deep-research-processing.md** - Execute Deep Research via ChatGPT Selenium

```
Tools:    Bash, Read, TodoWrite
Command:  uv run scripts/deepresearch_gpt.py --all
Purpose:  Executes deep research automation using Selenium to interact with ChatGPT.
          Collects comprehensive research data for all keywords.
```

### Phase 5: Research Optimization

> **5.1-deep-research-merge-data.md** - Markdown Token Optimizer

```
Tools:    Bash, Read, TodoWrite
Command:  uv run scripts/markdown_optimizer.py --all
Purpose:  Optimizes research markdown documents for token efficiency.
          Achieves 45-55% reduction while preserving content quality.
```

### Phase 6: Article Generation

> **6-post-plan-processing.md** - AI Article Generation Pipeline

```
Tools:    Bash, Read, TodoWrite
Command:  uv run -m bankcontent.postplan.main --arguments "Included citation"
Parallel: uv run -m bankcontent.postplan.main --parallel 5 --arguments "Included citation"
Purpose:  Generates full articles with citation support.
          Supports parallel processing for batch operations.
Params:   --parallel 5                     Process 5 keywords simultaneously
          --arguments "Included citation"  Enable citation inclusion
```

### Phase 7: SEO Optimization

> **7.0-meta-seo.md** - Parallel SEO Generation (Orchestrator)

```
Tools:    Task, TaskOutput, Bash
Timeout:  300000ms (5 minutes)
Purpose:  Orchestrates parallel generation of first sentences and meta descriptions
          using sub-agents for maximum efficiency.
Workflow: 1. Spawns two parallel sub-agents in single message
          2. Agent 1: uv run -m bankcontent.meta_seo.first_sentence --all
          3. Agent 2: uv run -m bankcontent.meta_seo.meta_description --all
          4. Aggregates results into unified report
```

> **7.1-first-sentence.md** - Generate SEO First Sentences

```
Tools:    Bash, Read, TodoWrite
Command:  uv run -m bankcontent.meta_seo.first_sentence --all
Purpose:  Generates SEO-optimized first sentences for all keywords.
          Creates engaging hooks that improve SERP click-through rates.
```

> **7.2-meta-description.md** - Generate SEO Meta Descriptions

```
Tools:    Bash, Read, TodoWrite
Command:  uv run -m bankcontent.meta_seo.meta_description --all
Purpose:  Generates SEO meta descriptions for all keywords.
          Creates compelling 150-160 character descriptions for search results.
```

### Phase 8: Image Generation

> **8.0-download-image-gdrive.md** - Download Images from Google Drive

```
Tools:    Bash, Read, TodoWrite
Command:  uv run scripts/image-gdrive.py
Purpose:  Downloads keyword-matched images from Google Drive for use as article visuals.
```

> **8.1-create-feature-image.md** - Generate Feature Images

```
Tools:    Bash, Read, TodoWrite
Command:  uv run scripts/create-feature-img-openrouter.py
Purpose:  Generates feature/hero images for articles using OpenRouter Gemini API.
          Creates visually compelling header images.
```

> **8.2-create-infographic.md** - Generate Infographic Images

```
Tools:    Bash, Read, TodoWrite
Command:  uv run scripts/create-infographic-img-openrouter.py
Purpose:  Generates infographic images via OpenRouter Gemini API.
          Creates data visualizations and informational graphics for article content.
```

> **8.3-resize-remove-exif-image.md** - Image Optimization

```
Tools:    Bash, Read, TodoWrite
Command:  uv run python scripts/re-size-image.py --all --type both -w 1080
Purpose:  Resizes images to WebP format and removes EXIF metadata for privacy
          and performance optimization.
Params:   --all         Process all keywords
          --type both   Process both feature and infographic images
          -w 1080       Target width of 1080 pixels
```

### Phase 9: Publishing

> **9.-pick-author.md** - WordPress Auto-Post

```
Tools:    Bash, Read, TodoWrite, Task
Command:  @specs/auto_post_prompt.md execute task
Purpose:  Picks appropriate author and executes WordPress auto-posting for
          completed articles. Handles content scheduling and publication workflow.
```
