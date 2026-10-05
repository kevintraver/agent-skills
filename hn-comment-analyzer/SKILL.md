---
name: hn-comment-analyzer
description: Finds Hacker News stories by title and fetches and summarizes their comment threads. Use when the user asks to "summarize HN comments", "summarize Hacker News discussion", "what are people saying on HN", "analyze HN thread", "fetch HN comments", or provides an HN story title, item ID, or news.ycombinator.com URL.
---

# HN Comment Analyzer

Fetch and summarize Hacker News discussions using the Algolia API.

## Fetching Comments

**IMPORTANT: ALWAYS quote the argument to prevent shell glob expansion.**

```bash
npx tsx ./scripts/fetch-hn-comments.ts "<url-or-id-or-title>"
```

**Examples:**

```bash
npx tsx ./scripts/fetch-hn-comments.ts "https://news.ycombinator.com/item?id=46654726"
npx tsx ./scripts/fetch-hn-comments.ts "46654726"
npx tsx ./scripts/fetch-hn-comments.ts "Ask HN: Is it still worth pursuing a software startup?"
npx tsx ./scripts/fetch-hn-comments.ts --title "1984"
```

Also works with bun: `bun run ./scripts/fetch-hn-comments.ts "<url-or-id-or-title>"`

For a title or title fragment, the script uses [HN Search](https://hn.algolia.com/) to search story titles only. Among the first 50 results, it prefers an exact title match ignoring case and extra whitespace; otherwise it chooses HN Search's highest-ranked result. Duplicate exact titles retain HN Search's ordering. Use `--title` to search a title that looks like a numeric ID or URL.

The selected title and HN item link are printed to stderr; stdout remains JSON. Check the returned title before summarizing and include the matched HN link when starting from a title. If it is the wrong thread, refine the title or use the intended thread's ID/link.

The script outputs JSON with the post metadata and nested comment tree.

Algolia comment `points` may be null or missing and are not a reliable basis for upvote rankings, point distributions, or claims of community agreement. Story points describe the post, not individual comments. Base the summary on recurring themes, substantive arguments, and reply activity.

## Summarization Workflow

1. **Fetch**: Run the script with the user's URL, ID, or title; verify the selected story for title searches
2. **Analyze**: Parse the JSON output, noting:
   - Returned readable comment count and depth of discussion (filtered parents can shorten reply chains)
   - Top-level comment themes
   - Recurring perspectives and the arguments supporting them
   - Nested reply chains (indicate debate/discussion)
3. **Summarize**: Generate the summary following the output format below

## Output Format

Structure your summary as follows:

### Main Takeaways

- 3-5 bullet points capturing the dominant themes/opinions
- Lead with recurring themes and substantive perspectives

### Sentiment Overview

- General tone (positive/negative/mixed/technical)
- Apparent agreement vs. disagreement in the available comments; do not infer community consensus from scores or reply counts

### Notable Points

- Contrarian or controversial takes (often in deeply nested threads)
- Expert insights (look for detailed technical comments)
- Interesting tangents worth mentioning

### Discussion Dynamics

- Brief note on engagement level and discussion style
- Any flame wars or heated debates to be aware of

## Tips

- **Comment scores**: Do not rank perspectives by upvotes or treat missing/null points as zero
- **Deep reply chains**: Often contain nuanced debate or corrections
- **Comments with no replies**: May be late additions or niche takes
- **Author replies**: The original poster's comments are especially relevant
- **Deleted/dead or unusable comments**: The script filters explicit `deleted`/`dead` flags, `[deleted]`/`[dead]` placeholders, and missing or blank text after stripping HTML. Readable descendants are promoted to the nearest retained ancestor (or the top level).
- **Moderation limits**: Algolia may omit moderation flags or items, so this filtering cannot identify every deleted/dead comment or establish moderation totals. Describe only the available readable discussion; do not interpret missing text as proof of deletion or claim all dead comments were removed.

## Error Handling

If the script fails:

- **"no matches found"**: URL wasn't quoted - always wrap URLs in double quotes
- **"No HN stories found for title"**: Try a shorter title fragment or provide the HN item URL/ID
- **"Failed to search HN titles"**: HN Search failed; retry after a moment or use a known item URL/ID
- Verify the URL is a valid HN item URL (news.ycombinator.com/item?id=...)
- Check the item ID exists (some items are deleted)
- The Algolia API may have rate limits; retry after a moment
