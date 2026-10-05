#!/usr/bin/env python3
"""Resolve a video page to one stream containing both audio and video."""

import argparse
import json
import subprocess
from urllib.parse import quote


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("url", help="Video page or broadcast URL")
  args = parser.parse_args()

  result = subprocess.run(
    [
      "yt-dlp",
      "--ignore-config",
      "--no-playlist",
      "--skip-download",
      "--dump-single-json",
      "--format",
      "b",
      "--",
      args.url,
    ],
    stdout=subprocess.PIPE,
    text=True,
  )
  if result.returncode:
    raise SystemExit(result.returncode)

  info = json.loads(result.stdout)
  if info.get("_type") in {"playlist", "multi_video"}:
    raise SystemExit("This page contains multiple videos; select a specific video URL.")

  stream_url = info["url"]
  print(json.dumps({
    "title": info.get("title"),
    "page_url": info.get("webpage_url", args.url),
    "stream_url": stream_url,
    "iina_url": "iina://weblink?url=" + quote(stream_url, safe=""),
    "width": info.get("width"),
    "height": info.get("height"),
    "protocol": info.get("protocol"),
    "is_live": info.get("is_live", False),
    "http_headers": info.get("http_headers", {}),
  }, indent=2))


if __name__ == "__main__":
  main()
