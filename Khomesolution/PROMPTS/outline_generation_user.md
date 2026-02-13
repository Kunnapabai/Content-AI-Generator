Generate a Koray-aligned SEO outline for keyword #{keyword_index}: "{keyword}"

## Source Context
{source_context}

## SERP Analysis Data
```yaml
{serp_analysis_yaml}
```

## Related Queries (from master-queries.csv)
{query_csv}

## Key Decision Factors
- Entity salience ranking: {top_entities}
- Primary intent: {primary_intent}
- Micro intents: {micro_intents}
- Dominant title patterns: {dominant_patterns}
- Title generation signals: {title_signals}
- Knowledge graph edges: {kg_edges}
- Opportunity gaps: {opportunity_gaps}

## Requirements Checklist
✓ Single H1 (macro context) - root node
✓ First H2 as answer-first question
✓ Contextual bridge H2 (info → decision)
✓ Antonym context H2 (drawbacks/limitations)
✓ 5+ H2 minimum
✓ Total headings (H1+H2+H3+H4) between 25-30
✓ No duplicate headings
✓ Language: {language}
✓ FAQ H3s don't repeat H2 text

⚠️ HARD LIMIT: Target 27 headings total (H1+H2+H3+H4). Acceptable range: 25-28. Anything over 28 or under 25 is REJECTED. Count before responding.

Output HTML heading tags only (h1-h4) with section comments: