---
name: iina-stream
description: Extract a playable stream URL from a video page or live broadcast for IINA. Use when given a video URL and asked for its direct media URL, an HLS stream, or a link to watch in IINA.
---

# IINA Stream

Turn the supplied video page URL into a fresh, playable media URL without
downloading the video. Return a direct stream link and an IINA launch link.

## Resolve the URL

Use the bundled helper, resolving its path relative to this skill directory:

```bash
python3 <skill-directory>/scripts/resolve_stream.py 'https://example.com/video'
```

It requires `yt-dlp` on PATH and selects `best`, a single format containing
both video and audio. The default yt-dlp selection can return separate video
and audio URLs; do not present a video-only URL as a complete playable stream.
If yt-dlp is missing, install it using the environment's package manager when
authorized (on macOS: `brew install yt-dlp`). Respect execution and network
approval requirements; a sandbox DNS failure is not evidence the video is gone.

Read the helper's JSON output for the title, quality, stream URL, IINA URL,
protocol, live status, and HTTP headers. For live broadcasts, use the exact
returned manifest URL, including query parameters. Do not fabricate a replay
URL by renaming a live playlist. Resolve afresh if the URL expires or playback
stops after the broadcast ends.

If extraction fails:

- Inspect the extractor error. For a post linking to a broadcast, resolve its
  actual broadcast page if the original post extractor did not follow it.
- If no combined format exists, look for a playable HLS or DASH manifest that
  includes both tracks, or offer the original page through IINA's yt-dlp
  integration and explain that a single direct stream was unavailable.
- For unsupported pages, use the available browser tool (prefer
  `agent-browser` when installed). Load its current usage guide, use a named
  session, open the supplied page, snapshot it, and start the video if needed.
  Inspect `<video>`/`<source>` URLs and captured media network requests for
  `.m3u8`, `.mpd`, or `.mp4`. A `blob:` URL only exists in that browser; find
  the underlying network manifest. Do not return individual media segments.
- If the page has multiple videos, select the user's intended item. If access
  needs authentication, use authorized session access; do not bypass DRM or
  access restrictions, export login cookies, or include secrets in the answer.

## Verify playback and return the result

When `ffprobe` is available, briefly probe the selected URL:

```bash
ffprobe -v error -rw_timeout 15000000 \
  -show_entries stream=codec_type,width,height -of json 'STREAM_URL'
```

Confirm both audio and video and report the actual resolution. If this fails,
check whether the extractor supplied required Referer or User-Agent headers;
retry with those headers and give an IINA CLI command with the corresponding
mpv options if bare-URL playback needs them. Never claim playback was verified
when only metadata extraction succeeded.

Return a clickable direct stream link, its quality, and an IINA link using
`iina://weblink?url=<percent-encoded-stream-url>`. The helper encodes the entire
nested URL, including `&`, `?`, and `#`. If the client will not open that scheme,
the user can paste the direct URL into IINA's **Open URL** dialog. Launch IINA
only when asked. Mention expiration only for live or temporary/signed URLs.

Reference: [yt-dlp format selection](https://github.com/yt-dlp/yt-dlp#format-selection).
