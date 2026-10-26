---
name: cleanup-chat-screenshot
description: Turn a raw chat screenshot (iMessage, Slack, WhatsApp, Discord, Signal, Messenger, and similar), or text from the conversation such as Claude's last reply, into a clean, shareable image on a rounded card, optionally removing messages, clutter, or private details. Use when asked to clean up, tidy, crop, or make shareable a chat screenshot, remove messages from one, or redact names, phone numbers, or avatars in one. Also use when asked to turn a reply, message, or pasted text into a screenshot or image for sharing ("tidy that up for sharing as a screenshot", "make that an image I can share").
---

# Clean up a chat screenshot

Turn a chat screenshot into a clean image that looks like an untouched capture of the conversation, presented on a card. Text with no screenshot behind it, such as Claude's last reply, gets rendered onto the same kind of card.

## Input

- The screenshot, or the text to share. "That" or "this" with no image in sight usually means Claude's last reply; if it could mean more than one thing, ask. For text, follow "From text" below instead of the steps.
- Optional instructions: messages to remove, clutter to drop, details to redact and how (solid block or blur), a target size.

With no instructions ("clean this up"), only crop and put it on the card. Suggest removals or redactions that seem useful, but don't make them.

## Steps

1. **Remove requested messages.** Cut out each message's full horizontal band and close the gap, so the spacing between the remaining bubbles looks natural. If the request clearly identifies the messages ("the last two"), just do it. If it's ambiguous which bubbles are meant, show a numbered preview of the bubbles and ask.
2. **Crop.** Trim cut-off bubbles at the top and bottom edges and the empty space around the conversation. This needs no confirmation; mention it in the reply.
3. **Drop clutter, only when asked:** "Read" receipts, timestamps, the typing indicator.
4. **Redact, only when asked:** cover names, phone numbers, avatars, or anything else the user names. Use solid blocks unless the user asks for blur. Blur heavily enough that the text can't be read. Whether or not redaction was requested, point out anything else that looks like personal information (names, phone numbers, email or street addresses, avatars, account or order numbers) and offer to redact it.
5. **Put it on a card.** Rounded corners, even padding, on a slightly darker background that matches the chat's theme (dark or light).
6. **Size.** If given a target size, scale down to fit within it. Never enlarge past the source.
7. **Check, then deliver.** Look at the result: no bubble clipped, gaps between bubbles even, nothing removed that shouldn't be. Save it as a new file where the user will find it, never overwriting the original or leaving it only in a temporary folder, and give the full path. If the environment can put images on the clipboard, copy it there too and say so. If the user just asked to have something else on the clipboard (such as the text this card was made from), say before copying that the image will replace it.

## From text

1. **Keep the text word for word**, with its structure (paragraphs, bullets, bold, code). Don't add a title or caption unless asked.
2. **Lay it out as an HTML card** in the scratchpad: system sans-serif, a line length that reads comfortably (about 560px), light theme unless asked otherwise, with the card styling from step 5. Reset default list and paragraph margins so the padding is actually even.
3. **Render at 2x** with `agent-browser`:
   ```bash
   agent-browser set viewport 900 600 2
   agent-browser open "file://$PWD/card.html"
   agent-browser screenshot "#card" out.png   # selector of the element wrapping card + background
   ```
4. Continue with steps 4 (point out personal information), 6, and 7.

## Rules

- Never repaint, invent, or reword message text or bubbles. Only cut, crop, cover, and blur. From text, render it exactly as written.
- Ask before removing anything the user didn't mention, except the edge crop in step 2.
- When anything is ambiguous, such as which message the user means, or how to handle a problem in the source like a bubble already cut off at the side, ask the user before acting instead of guessing.
