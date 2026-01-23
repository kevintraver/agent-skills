---
name: qmd
description: Search markdown knowledge bases with qmd (Quick Markdown Search). Use when searching notes, documentation, meeting transcripts, or any indexed markdown collections. Supports keyword search (qmd search), semantic search (qmd vsearch), and hybrid search with reranking (qmd query). Also use for managing collections, adding context, and retrieving documents.
---

# qmd - Quick Markdown Search

On-device search engine for markdown knowledge bases combining BM25 full-text search, vector semantic search, and LLM re-ranking.

## Search Commands

```bash
# Fast keyword search (BM25)
qmd search "authentication flow"

# Semantic vector search
qmd vsearch "how to login"

# Hybrid search with reranking (best quality, slower)
qmd query "user authentication"
```

### Search Options

```bash
-n <num>              # Number of results (default: 5)
-c, --collection <n>  # Restrict to specific collection
--min-score <num>     # Minimum score threshold
--full                # Show full document content
--json                # JSON output for processing
--files               # Output: docid,score,filepath,context
--all                 # Return all matches
```

### Before Searching, Ask Yourself

1. **Do I know the exact terms?** → `search` (BM25 rewards exact matches)
2. **Am I exploring a concept?** → `vsearch` (semantic similarity)
3. **Is this a critical lookup?** → `query` (but only after cheaper methods fail)
4. **Which collection contains this?** → Use `-c` to scope and reduce noise

### Search Strategy Selection

**Use `search` (BM25) when:**
- Exact identifiers: function names, error codes, file paths, proper nouns
- Known terminology where synonyms would add noise
- Iterative exploration—start here, refine based on results
- Quick existence checks ("do I have notes on X")

**Use `vsearch` when:**
- Conceptual queries: "how does X work" rather than exact term "X"
- User might not know correct terminology
- Cross-referencing ideas expressed differently across documents
- Natural language questions about meaning

**Use `query` ONLY when:**
- High-stakes search where quality matters more than speed
- Previous methods returned poor or ambiguous results
- Need best single match from large collection

`query` runs 5 stages (FTS + vector + query expansion + RRF fusion + LLM reranking) using 3 local models. Reserve for final passes.

**Default strategy: `search` first → escalate to `vsearch` → reserve `query` for important searches.**

### Query Formulation

| Mode | Good Query | Bad Query | Why |
|------|------------|-----------|-----|
| `search` | `"handleAuth"` | `"how does auth work"` | BM25 matches tokens literally |
| `search` | `error 404 nginx` | `"what causes errors"` | More keywords = better BM25 |
| `vsearch` | `"how to handle user login"` | `handleAuth` | Semantic search needs natural language |
| `vsearch` | `"meeting about Q3 roadmap"` | `Q3` | Single tokens lose semantic context |
| `query` | Any | — | Query expansion handles reformulation |

**For `search`**: use specific identifiers, error messages, function names, multiple keywords.
**For `vsearch`**: use natural questions, full phrases, describe what you're looking for.
**For `query`**: query expansion generates variations, so exact phrasing matters less.

## NEVER

- **Run `vsearch` or `query` without embeddings** — returns empty or garbage results. Run `qmd status` first to verify embeddings exist, or `qmd embed` to generate.
- **Use `query` in tight loops** — each call runs query expansion + reranking through 3 LLMs. Use `search` for iteration.
- **Compare scores across search types** — BM25, vector, and reranker use different normalization. A 0.7 from `search` ≠ 0.7 from `vsearch`.
- **Ignore docids** — search results show 6-char hashes (e.g., `#a1b2c3`). Use these with `qmd get "#a1b2c3"` for reliable retrieval instead of fuzzy path matching.
- **Skip `--min-score` for large exports** — `--all` without score filtering returns noise. Use `--min-score 0.3` minimum.
- **Add overlapping collection paths** — causes duplicate indexing and inconsistent results.

## Document Retrieval

```bash
qmd get "#abc123"                    # By docid (preferred - from search results)
qmd get notes/meeting.md             # By filepath (fuzzy matched)
qmd get notes/meeting.md:50 -l 100   # Start at line 50, max 100 lines
qmd multi-get "docs/*.md"            # Multiple by glob
qmd multi-get "a.md, b.md, #abc123"  # Multiple by list
```

**Prefer docids over paths** — docids from search results are stable; paths use fuzzy matching which can be ambiguous.

## Setup & Maintenance

```bash
# Collections
qmd collection add ~/notes --name notes --mask "**/*.md"
qmd collection list
qmd ls <collection>

# Context (helps search understand content purpose)
qmd context add qmd://notes "Personal notes and ideas"

# Required for vsearch/query
qmd embed              # Generate embeddings (~3GB models auto-download)
qmd update             # Re-index after file changes
qmd status             # Check index health and embedding status
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `vsearch` returns empty | No embeddings generated | `qmd embed` |
| `query` returns empty | No embeddings + needs models | `qmd embed`, models auto-download on first use |
| Good doc ranks low in `query` | Reranker disagreed with retrieval | Use `search` for exact-match queries |
| Stale results after edits | Index not updated | `qmd update` |
| Slow first `query` | Models downloading (~3GB) | Wait for download, cached after |
| Different scores same doc | Searched with different method | Scores not comparable across methods |

## Score Interpretation

Scores are normalized 0-1 but backends differ:
- **BM25** (`search`): term frequency based, high scores = exact keyword matches
- **Vector** (`vsearch`): semantic similarity, high scores = conceptually related
- **Hybrid** (`query`): blended RRF + reranker, most reliable for relevance

| Score | Meaning |
|-------|---------|
| 0.8+ | Highly relevant — likely what you want |
| 0.5 - 0.8 | Moderately relevant — worth reviewing |
| 0.3 - 0.5 | Tangentially relevant — may contain useful context |
| < 0.3 | Low relevance — usually noise |

## Agent Workflows

**Iterative search pattern (recommended):**
```bash
# 1. Quick scan with BM25
qmd search "auth" --files -n 10
# 2. Read promising docs by docid
qmd get "#a1b2c3"
# 3. If results weak, escalate to semantic
qmd vsearch "user login flow" --files -n 5
```

**Bulk context gathering:**
```bash
# Get all relevant docs above threshold, output for LLM processing
qmd search "config" --json --all --min-score 0.3 -c project-docs
```

**Scoped search (when collection known):**
```bash
qmd search "API" -c docs -n 10
```

**Named indexes for separate knowledge bases:**
```bash
qmd --index work search "quarterly reports"
qmd --index personal search "recipes"
```

## MCP Server

MCP tools mirror CLI: `qmd_search`, `qmd_vsearch`, `qmd_query`, `qmd_get`, `qmd_multi_get`, `qmd_status`

Config: `{ "mcpServers": { "qmd": { "command": "qmd", "args": ["mcp"] } } }`

Data: `~/.cache/qmd/` (index.sqlite + ~3GB models)
