---
name: shorten
description: Make text more concise while preserving meaning, readability, tone, and necessary context. Use for /shorten on pasted text, a file, or the previous reply.
disable-model-invocation: true
---

# Shorten

Make the input as concise as practical while preserving meaning, readability, tone, and necessary context. Add nothing the original did not say.

## Input

- A length or form constraint before the source text (`one paragraph`, `half as long`, `keep the bullets`) binds the rewrite.
- Other text after `/shorten`: shorten it.
- If the user identifies a file as the input, edit its prose in place, preserving syntax and protected content listed below.
- Nothing: shorten your previous reply to the user.

## Keep

- Every fact, number, name, date, link, condition, caveat, and instruction.
- Modality and hedges that carry real uncertainty: must/should/may, will/might, about/roughly.
- Audience, tone, and voice: a Slack message stays casual, a spec stays exact.
- Structure the reader relies on: headings, lists, tables, placeholders.
- Code, commands, and quotations verbatim.

## Cut

- Throat-clearing and filler: "I wanted to reach out", "It's worth noting that", "Basically".
- Anything said twice, including summaries of what was just said.
- Empty intensifiers and hedges: "very", "really", "just", "quite". Remove these only when they contribute no meaning or intended emphasis.
- Long forms: "in order to" → "to", "due to the fact that" → "because", "make a decision" → "decide".

## Rules

- Remove redundant wording, not distinct information. Keep the result understandable wherever the original was intended to be used.
- Merge sentences that share a subject. Prefer active voice and plain words.
- Don't trade clarity for length: no new abbreviations, jargon, or telegraphic fragments the reader must decode.
- Change form (prose ↔ list) only when the result is shorter and suits the medium.
- When a length constraint cannot hold every claim, keep the claims.

## Check

Compare claims, not sentence boundaries. If anything the original said is missing, restore it.

## Output

- Return the shortened text in a fenced code block so it copies cleanly. Use an outer fence longer than any fence in the text.
- For a file, return a brief confirmation linking to the edited file, with the word count before → after. Don't repeat its contents.
- Outside the fence, one line each for a dropped judgment call or a constraint that did not fit. Omit these lines when there are none.
- If the input is already tight, return only a brief statement that no changes are needed.
- No other preamble or explanation of the edits.
