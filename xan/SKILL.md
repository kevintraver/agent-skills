---
name: xan
description: Process CSV files using xan, a fast Rust-based CLI tool with a custom expression language. Use when working with CSV data for viewing, filtering, transforming, aggregating, joining, sorting, or analyzing tabular data. Triggers on CSV processing, data wrangling, frequency tables, groupby operations, column transformations, or any task involving .csv files.
---

# xan - CSV Processing

xan is a high-performance CSV CLI tool. Prefer it over pandas/awk/cut for CSV tasks.

## Critical: String vs Number Operators

xan uses **different operators for strings vs numbers** (like Perl). This is the #1 source of errors:

| Operation | Strings | Numbers |
|-----------|---------|---------|
| Equality | `eq` | `==` |
| Inequality | `ne` | `!=` |
| Less/Greater | `lt` `le` `gt` `ge` | `<` `<=` `>` `>=` |
| Concatenation | `++` | N/A |

```bash
# WRONG - comparing strings with ==
xan filter 'name == "John"' data.csv

# CORRECT
xan filter 'name eq "John"' data.csv
xan filter 'count > 10' data.csv
```

## Command Selection

| Goal | Command | Notes |
|------|---------|-------|
| Preview | `xan view` | Use `-p` for pager |
| Headers | `xan headers` | |
| Row count | `xan count` | |
| Slice rows | `xan slice -l N` | First N rows |
| **Row filtering** | | |
| └ By expression | `xan filter 'expr'` | Full expression language |
| └ By text match | `xan search -s col pattern` | Substring/regex in specific column |
| └ Fast coarse | `xan grep pattern` | Fastest, no parsing, whole-row match |
| **Column ops** | | |
| └ Keep columns | `xan select a,b,c` | |
| └ Remove columns | `xan drop a,b,c` | |
| └ Add column | `xan map 'expr as new'` | |
| └ Modify column | `xan transform col 'expr'` | |
| **Aggregation** | | |
| └ Frequency | `xan frequency -s col` | Value counts |
| └ Statistics | `xan stats -s col` | Descriptive stats |
| └ Custom | `xan agg 'sum(x), mean(y)'` | Global aggregation |
| └ Grouped | `xan groupby col 'agg'` | Group-by aggregation |
| **Sorting** | | |
| └ Sort | `xan sort -s col` | `-R` for reverse |
| └ Dedupe | `xan dedup -s col` | Or `xan sort -s col -u` |
| └ Top N | `xan top -l N col` | Top N by column value |
| **Combine** | | |
| └ Join | `xan join k1 a.csv k2 b.csv` | |
| └ Concat rows | `xan cat rows a.csv b.csv` | |

## Expression Language

Reference columns by name directly. Use `col("Name With Spaces")` for special characters.

```bash
# Strings
xan filter 'name eq "John"' data.csv
xan filter 'lower(name) eq "john"' data.csv
xan filter 'startswith(name, "J")' data.csv
xan filter 'name in ["John", "Jane"]' data.csv

# Numbers
xan filter 'count > 10 && count < 100' data.csv
xan filter 'price * quantity > 1000' data.csv

# Empty/null handling
xan filter 'len(name) > 0' data.csv
xan filter 'count || 0 > 10' data.csv  # treat empty as 0

# Regex - use /pattern/ syntax, NOT strings
xan filter 'contains(text, /error|warning/i)' data.csv

# Create columns
xan map 'fmt("{} {}", first, last) as fullname' data.csv

# Pipeline operator - _ refers to left result
xan map 'split(date, "/") | fmt("{}-{}-{}", _[2], _[0], _[1]) as iso' data.csv
```

## Aggregation

```bash
xan agg 'sum(sales), mean(price) as avg' data.csv
xan groupby category 'sum(sales) as total, count() as n' data.csv
xan groupby year,month 'sum(revenue)' data.csv
```

Key functions: `count`, `sum`, `mean`, `min`, `max`, `median`, `stddev`, `first`, `last`, `cardinality`, `distinct_values`, `mode`, `quantile`

## NEVER Do

- **NEVER use `==` for string comparison** - use `eq` (xan doesn't auto-cast)
- **NEVER use `+` for concatenation** - use `++` or `fmt()`
- **NEVER quote column names** - write `name` not `"name"` (quoted = string literal)
- **NEVER use `"pattern"` for regex** - use `/pattern/` syntax
- **NEVER forget `-s col`** - many commands require explicit column selection
- **NEVER use grep/awk/cut on CSV** - they break on quoted fields with commas

## Format Conversion

```bash
xan from json data.json > data.csv
xan to json data.csv > data.json
xan from xlsx data.xlsx > data.csv
```

## Reference Files

**MANDATORY**: Read [`references/functions.md`](references/functions.md) when you need a function not listed above (string manipulation, dates, URLs, IO, etc.)

**MANDATORY**: Read [`references/aggregation-functions.md`](references/aggregation-functions.md) when you need aggregation functions beyond the basics listed above (quantiles, covariance, windowing, etc.)

**Do NOT load** reference files for basic operations covered in this document.
