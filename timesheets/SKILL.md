---
name: timesheets
description: "Manage contractor timesheets and generate PDF invoices from them. Use whenever the user mentions invoices, billing, timesheets, logging hours, unbilled/unsubmitted hours, or marking work as submitted. Trigger on phrases like 'build an invoice', 'bill the client', 'invoice for unsubmitted hours', 'move everything to submitted', 'add hours for Thursday', 'log time', 'put that on my timesheet', or any request to turn tracked hours into a payment document. Also trigger when the user asks what they haven't billed yet, or wants to adjust hours before invoicing."
---

# Timesheets & Invoicing

Manages the full lifecycle of contractor hours: logging them, invoicing them, and archiving them once submitted.

## The core model

Hours live in per-client CSV files. A file's **location** is what marks it billed or unbilled — there is no status column:

```
Timesheets/
├── Acme/
│   ├── week-of-2026-03-16.csv     ← unbilled (client root)
│   ├── Invoice_Acme_20260313.pdf
│   └── submitted/
│       └── week-of-2026-03-09.csv ← already billed
└── Globex/
    └── submitted/
```

CSVs have the header `Date,Hours,Description` and are named `week-of-YYYY-MM-DD.csv` after the first day of the billing period they start — not necessarily a Monday. The client root normally holds one open file; new hours go there until it's invoiced and archived, so a file can span more than a week. Don't assume the filename bounds the dates inside.

This location-as-status model is why the archive step matters: if billed CSVs stay in the client root, the next invoice double-bills them.

## Client and sender details

This skill holds no client names, rates, contacts, or sender details. Take them from the user's local notes (e.g. `CLAUDE.local.md` or memory) or from past invoices in the client folder. If one is missing, ask rather than guess.

## Generating an invoice

Everything in the client root is unbilled by definition, so the normal case is a glob. The script needs `reportlab`; if it isn't installed, run it as `uv run --no-project --with reportlab python3 <skill>/scripts/invoice.py ...`.

```bash
python3 <skill>/scripts/invoice.py \
  --client "<Client name>" \
  --rate <hourly rate> \
  --csvs /path/to/Timesheets/<Client>/*.csv \
  --output /path/to/Timesheets/<Client>/Invoice_<Client>_YYYYMMDD.pdf \
  --invoice-num INV-YYYY-NNN \
  --date YYYY-MM-DD \
  --from-name "<Your name>" \
  --from-email "<you@example.com>"
```

Read the CSVs first and show the user the totals. They often catch a wrong day before it goes out — that moment is cheaper than reissuing.

While reading them, glance at `submitted/` for rows with the same date, hours, and description as a root row. Location is the source of truth, so this is rare — but archiving sometimes half-fails, and a row that already went out on an earlier invoice is the one error the client will notice. Flag it and ask rather than silently billing or dropping it.

**Rate**: the client's established hourly rate (see Client and sender details).

**Invoice number**: sequential `INV-YYYY-NNN`. Check existing `Invoice_*.pdf` filenames in the client folder (and `submitted/`) to find the last one used.

**Filename**: `Invoice_<CLIENT>_<YYYYMMDD>.pdf`, dated the day it's sent.

### Script options

| Flag | Description | Default |
|------|-------------|---------|
| `--client` | Name for "Bill To" | required |
| `--rate` | Hourly rate | required |
| `--csvs` | CSV paths (glob-friendly) | required |
| `--output` / `-o` | Output PDF path | `Invoice_<client>_<date>.pdf`, using `--date` |
| `--invoice-num` | Invoice number | required |
| `--date` | Invoice date (YYYY-MM-DD) | today |
| `--from-name` | Sender name | required |
| `--from-email` | Sender email | none |
| `--no-consolidate` | Keep same-day entries as separate rows | off |

Same-day entries merge into one row by default, descriptions joined with `; `. This keeps a 50-line timesheet readable as a 20-line invoice.

### Layout

Header (no rule line under it), From/Bill-To, a summary box (total hours, rate, period as `Mon DD – Mon DD, YYYY` (both years shown when it spans two), amount due), then the time log grouped by month with per-month subtotals. **Line items show hours only — no per-row dollar amounts.** The dollar total appears once at the bottom. This is deliberate: it keeps the client's attention on the total rather than auditing each row.

Style changes (colors, fonts, spacing) go in `scripts/invoice.py` — the color constants sit at the top of the file.

## Adding or adjusting hours

When the user gives hours conversationally ("8 hours Thursday for migration"), resolve weekday names against today's date, then append with the bundled script rather than writing CSV rows by hand:

```bash
<skill>/scripts/add_entry.sh /path/to/Timesheets/<Client> <hours> "<description>" [YYYY-MM-DD]
```

- The date defaults to today. Hours are written as given (`2` becomes `2.0`, `1.25` stays `1.25`).
- It appends to the open `week-of-*.csv`, fixing a missing trailing newline first, and quotes the description.
- No open file (the last period was archived): it starts `week-of-<date>.csv` and says so — tell the user.
- Exit 2: more than one file is open. Ask which period the hours belong to and edit that file directly.
- Report the open period's total from its last line, plus the amount at the client's rate.

**Descriptions** appear on the client's invoice. Write a few plain words naming the feature or area of work ("Checkout redesign", "Search performance fixes"), never tools, scripts, file names, PR numbers, or step-by-step verbs. If the user doesn't give one, derive it from the work in the conversation or recent commits at that same level of generality, and show them what you wrote.

When they correct a day's total ("I only worked 6 hours on the 12th"), adjust the existing rows rather than appending a correction row. If the day has several entries, trimming the largest is usually right — but say which row you changed and what the new grand total is, since a correction that silently preserves the total may not be what they meant.

## Archiving after submission

Only after the user confirms they actually sent it — "ok it's submitted", "move everything to submitted". Generating an invoice is not submission; they may still revise it.

Use the bundled script rather than `mv`:

```bash
python3 <skill>/scripts/archive.py /path/to/Timesheets/<Client>
```

It moves every CSV in the client root into `submitted/`. The same `week-of-*.csv` name can already exist there when a week spans two invoices: billed Mon–Tue on one, then Wed–Fri on the next. A plain `mv` would silently destroy the already-billed entries, so the script merges the two files by date instead. Tell the user about any merges it reports.

## Answering "what's unbilled?"

List the client root CSVs and sum their hours. No invoice needed unless they ask for one.

## CSV format

```
Date,Hours,Description
2026-03-16,2.0,"Onboarding flow, bug fixes"
```

Dates parse as `YYYY-MM-DD`, `Mon DD YYYY`, `Mon DD, YYYY`, `MM/DD/YYYY`, or `MM/DD/YY`. Rows with `Date` of `TOTAL` or empty `Hours` are skipped, so legacy files with summary rows load cleanly. Any other row with an unparseable date or hours stops the script, since dropping it would underbill; fix the row and rerun.

## Email to send with an invoice

Short is right — the PDF carries the detail:

> **Subject:** Invoice INV-YYYY-NNN — <Your name> (<Month YYYY>)
>
> Hi <client contact>,
>
> Attached is my invoice for <period start> – <period end>: <total hours> hours, <amount due>.
>
> Let me know if you have any questions.
>
> Thanks,
> <Your first name>
