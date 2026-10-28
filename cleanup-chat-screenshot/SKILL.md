---
name: cleanup-chat-screenshot
description: Turn a raw chat screenshot (iMessage, Slack, WhatsApp, Discord, Signal, Messenger, and similar), or text from the conversation such as your last reply, into a clean, shareable image on a rounded card, optionally removing messages, clutter, or private details. Use when asked to clean up, tidy, crop, or make shareable a chat screenshot, remove messages from one, or redact names, phone numbers, or avatars in one. Also use when asked to turn a reply, message, or pasted text into a screenshot or image for sharing ("tidy that up for sharing as a screenshot", "make that an image I can share").
---

# Clean up a chat screenshot

Turn a chat screenshot into a clean image that looks like an untouched capture of the conversation, presented on a card. Text with no screenshot behind it, such as your last reply, gets rendered onto the same kind of card.

## Input

- The screenshot, or the text to share. "That" or "this" with no image in sight usually means your last reply; if it could mean more than one thing, ask.
- Optional instructions: messages to remove, clutter to drop, details to redact and how (solid block or blur), a target size.

With no instructions ("clean this up"), only crop and put it on the card. Suggest removals or redactions that seem useful, but don't make them.

## What the result should look like

- **Removed messages leave no trace.** The remaining bubbles sit with natural, even spacing, as if the removed ones were never there. If the request clearly identifies the messages ("the last two"), just do it. If it's ambiguous which bubbles are meant, show the user the bubbles numbered and ask.
- **Tightly cropped.** No bubbles cut off at the top or bottom edge, and no empty space around the conversation. This needs no confirmation; mention it in the reply.
- **Clutter gone, only when asked:** "Read" receipts, timestamps, the typing indicator.
- **Private details unreadable, only when asked:** names, phone numbers, avatars, or anything else the user names, covered with solid blocks unless the user asks for blur. Blurred text must not be readable. Whether or not redaction was requested, point out anything else that looks like personal information (names, phone numbers, email or street addresses, avatars, account or order numbers) and offer to redact it.
- **On a card.** Rounded corners, even padding, on a slightly darker background that matches the chat's theme (dark or light).
- **Sized to fit** a target size if one was given. Never enlarged past the source.

## From text

- **Word for word**, with its structure (paragraphs, bullets, bold, code). No title or caption unless asked.
- **Easy to scan.** When paragraphs each open with a short label and a colon, show them as a bulleted list with each label in bold. Adding formatting like this is fine; changing the words is not.
- **Reads like clean typeset text:** a plain sans-serif, a comfortable line length, light theme unless asked otherwise, sharp at high resolution, on the same card as above.
- The personal-information check, sizing, and delivery apply here too.

## Delivery

Before handing it over, look at the result: no bubble clipped, gaps between bubbles even, nothing removed that shouldn't be. Save it as a new file where the user will find it, never overwriting the original or leaving it only in a temporary folder, and give the full path. If the image can be put on the clipboard, copy it there too and say so. If the user just asked to have something else on the clipboard (such as the text this card was made from), say before copying that the image will replace it.

## Rules

- Never repaint, invent, or reword message text or bubbles. Only cut, crop, cover, and blur. From text, keep the words exactly as written; only the formatting may change.
- Ask before removing anything the user didn't mention, except the edge crop.
- When anything is ambiguous, such as which message the user means, or how to handle a problem in the source like a bubble already cut off at the side, ask the user before acting instead of guessing.
