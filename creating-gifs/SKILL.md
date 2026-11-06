---
name: creating-gifs
description: Generates animated GIFs from text prompts with the `ai` CLI and GPT Image 2.6. Use when asked to make, create, or generate a GIF, an animated loop, or a reaction GIF.
---

# Creating GIFs

Requires the `ai` CLI (`npm i -g ai-cli`) and `AI_GATEWAY_API_KEY`.

GIFs work from text prompts only. With a reference image (`-i`), the Gateway
rejects GIF output with `invalid openai provider options`.

## Workflow

1. Write a prompt that describes the subject, one simple motion, and how it
   returns to its starting pose, so the loop is seamless.

2. Generate the GIF in zsh or bash:

   ```bash
   ai image "A robot waves, then returns to its starting pose. Smooth loop." \
     -m openai/gpt-image-2.6-flare -o out/ \
     --provider-options <(echo '{"openai":{"outputFormat":"gif","frameCount":9,"quality":"low"}}') \
     < /dev/null
   ```

3. Copy the saved GIF to the clipboard.

## Options

- `frameCount`: 2–16, default 9.
- `frameDurationMs`: 20–2000 per frame, default 200.
- `quality`: start with `low`.
