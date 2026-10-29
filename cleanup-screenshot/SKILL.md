---
name: cleanup-screenshot
description: Turn a screenshot (usually a chat) into a clean, shareable image on a card, with cropping, removals, and private details pixelated. Use when asked to clean up, tidy, crop, redact, or make shareable a screenshot or text.
---

# Clean up a screenshot

Make a screenshot, usually a chat, look like an untouched capture, presented on a card. Text with no screenshot behind it, such as your last reply, goes on the same card.

## Input

The screenshot or text, plus optional instructions: what to remove, what to cover and how (pixelated or solid block), a target size. "That" with no image in sight usually means your last reply; ask if it could mean more than one thing.

With no instructions, only crop, cover contact and account details, and put it on the card. Suggest other changes; don't make them.

## Edit or recreate

Work on the original when the job is cropping, covering, or removing whole messages. Recreate the conversation when a change would rearrange what's inside it: removing part of a message, adding or regrouping under a sender's name, the compact layout, or fixing a cut-off bubble. A recreation matches the app's look (theme, bubble colors and shape, a similar font, names and times as shown), keeps every word exactly as written, and is called a recreation in the reply. Other screenshots are only edited; if a request would add to one, say so instead.

Decide from the request's wording. With no instructions, or for text with no screenshot, there's nothing to decide. When the wording doesn't settle it, check with Vercel AI Gateway decision models, giving each the rule above and the two options, edit or recreate:

1. A text-only model, given a one-line description of the screenshot (the app, and whether it's a chat) and the request.
2. If that answer isn't confident (below about 0.7), a model that accepts images, given the screenshot and the request.
3. If it's still unsure, ask the user.

A model that errors or can't take the input counts as unavailable; go to the next step.

## Chat result

- **Cropped tight**, without asking: drop cut-off messages, app interface (status bar, contact header, message box, keyboard), and empty space. Keep a message clipped so little it still looks whole. Mention what the crop removed, including any name or avatar, and any barely clipped message kept.
- **Removals leave no trace**, with natural, even spacing. Do clear requests; for ambiguous ones (such as "the last two" when the bottom message is cut off or followed by a typing indicator), number the messages and ask. If a removal leaves a trace, such as a bubble losing its group's tail, say so and offer a recreation.
- **Regrouping, offered:** when messages lose their sender's name and picture (removed, or cut off above), offer to regroup them under the sender, noting that the time beside the name belongs to the message it first sat on.
- **Capture leftovers** (hover highlight, selected text, cursor, focus outline): point them out and ask. If the user agrees, shade a highlighted background to match, or recreate when text is affected.
- **Clutter, only when asked:** read receipts, timestamps, the typing indicator, unread markers (a "New" line), and app notices (huddle summaries, "joined the channel"). Offer to remove markers and notices when present.
- **Private details:** always cover email addresses, phone numbers, street addresses, and account or order numbers unless told to keep them, and list each one. Cover names, avatars, or anything else only when asked, but point out other personal information (names, avatars, places) and offer. Pixelate coarsely enough that text can't be read or reconstructed (solid blocks on request): the whole bubble, tail included, when the whole message is private; otherwise just the private part.
- **Card:** rounded corners and even padding, on a transparent background. If the user asks for a background, match the theme, slightly darker, or slightly lighter when the chat is black.
- **Compact layout, offered** for very wide screenshots: bring each side's messages in to the longest message's width, keeping date lines centered and vertical spacing unchanged.
- **Size:** fit any target size; never enlarge past the source.

## Other screenshots

App windows, popovers, notifications, settings panels, and receipts get the same treatment, with the subject in place of the conversation. Crop to the complete subject, dropping window edges, stray bits of other apps, and cut-off neighbors; ask if the subject is unclear. Remove parts on request the way messages are removed. Regrouping, the compact layout, and chat clutter don't apply.

## From text

Word for word, keeping its structure (paragraphs, bullets, bold, code), with no title or caption unless asked. When two or more paragraphs start with a short label and a colon, make those a bulleted list with bold labels and leave the rest. Plain sans-serif, comfortable line length, light theme unless asked, sharp at high resolution, on the same card. Private details, size, and delivery apply.

## Delivery

Check the result: nothing clipped, even gaps, nothing wrongly removed, no unmentioned edit, covered text unreadable, and text matching word for word. Save it as a new PNG, so transparency survives, where the user will find it, never over the original or only in a temporary folder, give the full path, and copy it to the clipboard if possible, saying so.

## Rules

- Never invent or reword text. Edit the original only by cutting, cropping, and covering; anything more is a recreation. From text, only the formatting may change.
- Recreate when the request needs it, decided as above. Only on the user's request or OK: regroup under a sender, shade a highlight, or use the compact layout.
- Ask before removing anything the user didn't mention, except the crop and covering contact or account details.
- When anything is ambiguous, such as which message is meant or a problem in the source like a message cut off at the side, ask instead of guessing.
