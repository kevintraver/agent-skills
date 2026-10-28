---
name: cleanup-chat-screenshot
description: Turn a raw chat screenshot (iMessage, Slack, WhatsApp, Discord, Signal, Messenger, and similar), or text from the conversation such as your last reply, into a clean, shareable image on a rounded card, optionally removing messages, clutter, or private details. Use when asked to clean up, tidy, crop, or make shareable a chat screenshot, remove messages from one, or redact or pixelate names, phone numbers, or avatars in one. Also use when asked to turn a reply, message, or pasted text into a screenshot or image for sharing ("tidy that up for sharing as a screenshot", "make that an image I can share").
---

# Clean up a chat screenshot

Turn a chat screenshot into a clean image that looks like an untouched capture of the conversation, presented on a card. Text with no screenshot behind it, such as your last reply, gets rendered onto the same kind of card.

## Input

- The screenshot, or the text to share. "That" or "this" with no image in sight usually means your last reply; if it could mean more than one thing, ask.
- Optional instructions: messages to remove, clutter to drop, details to cover and how (pixelated or solid block), a target size.

With no instructions ("clean this up"), only crop, cover contact and account details, and put it on the card. Suggest removals or redactions that seem useful, but don't make them.

## What the result should look like

- **Removed messages leave no trace.** The remaining messages sit with natural, even spacing, as if the removed ones were never there. When a removal leaves a trace that only repainting could hide, such as a bubble losing the tail that marked the end of its group, leave it and tell the user. When messages are left without their sender's name and picture, because the removed message carried them or they were cut off above, offer to move the name and picture up so the messages read as one group again. Mention that the time shown beside the name belongs to the message it originally sat on. If the request clearly identifies the messages, just do it. If it's ambiguous which ones are meant, such as "the last two" when the bottom message is cut off or followed by a typing indicator, show the user the messages numbered and ask.
- **Tightly cropped.** No messages cut off at the top or bottom edge, no app interface around the conversation (status bar, contact header, message box, keyboard), and no empty space. This needs no confirmation; mention it in the reply, including any name or avatar the crop removed.
- **Capture leftovers fixed, only when the user agrees:** traces of where the mouse or keyboard was when the screenshot was taken, such as a message highlighted on hover, selected text, a cursor, or a focus outline. Point them out and ask. If the user agrees, fix them only where that doesn't mean redrawing text, such as shading a highlighted background to match the rest, and say what had to stay.
- **Clutter gone, only when asked:** "Read" receipts, timestamps, the typing indicator.
- **Private details pixelated.** Cover them with pixelation coarse enough that the text can't be read or reconstructed, or with solid blocks if the user asks. When a whole message is private, pixelate the entire bubble, edges and tail included. When only part is, pixelate just that part so the rest still reads.
- **Contact and account details always covered:** email addresses, phone numbers, street addresses, and account or order numbers, without asking, unless the user says to keep them. List each one covered in the reply.
- **Other private details covered only when asked:** names, avatars, or anything else the user names. Whether or not covering was requested, point out anything else that looks like personal information (names, avatars, places) and offer to cover it.
- **On a card.** Rounded corners, even padding, on a background that matches the chat's theme (dark or light) and sets the card apart: slightly darker, or slightly lighter when the chat is already black.
- **Sized to fit** a target size if one was given. Never enlarged past the source.

## From text

- **Word for word**, with its structure (paragraphs, bullets, bold, code). No title or caption unless asked.
- **Easy to scan.** When two or more paragraphs open with a short label and a colon, show those as a bulleted list with each label in bold, and leave the other paragraphs as they are.
- **Reads like clean typeset text:** a plain sans-serif, a comfortable line length, light theme unless asked otherwise, sharp at high resolution, on the same card as above.
- The personal-information check, sizing, and delivery apply here too.

## Delivery

Before handing it over, look at the result: no message clipped, gaps between messages even, nothing removed that shouldn't be, no sign of an edit left unmentioned, covered text can't be read, and for text, every word matches the source. Save it as a new file where the user will find it, never overwriting the original or leaving it only in a temporary folder, and give the full path. If the image can be put on the clipboard, copy it there too and say so.

## Rules

- Never repaint, invent, or reword message text or bubbles. Only cut, crop, and cover (pixelate, or solid blocks on request), plus moving a sender's name and picture or shading a highlighted background to match, once the user agrees. From text, keep the words exactly as written; only the formatting may change.
- Ask before removing anything the user didn't mention, except the crop and covering contact and account details.
- When anything is ambiguous, such as which message the user means, or how to handle a problem in the source like a message already cut off at the side, ask the user before acting instead of guessing.
