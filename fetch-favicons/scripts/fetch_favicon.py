#!/usr/bin/env python3
"""
Fetch favicon for a domain using multiple fallback sources.

Usage:
    python fetch_favicon.py example.com
    python fetch_favicon.py example.com --output ./icons/
    python fetch_favicon.py example.com --size 128
"""

import argparse
import os
import sys
from urllib.parse import urlparse

if sys.version_info < (3, 6):
    print("Error: Python 3.6+ is required", file=sys.stderr)
    sys.exit(1)

import requests


def extract_domain(url_or_domain: str) -> str:
    """Extract domain from URL or return as-is if already a domain."""
    if "://" in url_or_domain:
        parsed = urlparse(url_or_domain)
        return parsed.netloc
    return url_or_domain.split("/")[0]


def fetch_from_google(domain: str, size: int = 128) -> bytes | None:
    """Fetch favicon from Google's favicon service."""
    url = f"https://www.google.com/s2/favicons?domain={domain}&sz={size}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and len(response.content) > 100:
            return response.content
    except requests.RequestException as e:
        print(f"Google fetch failed: {e}", file=sys.stderr)
    return None


def fetch_from_duckduckgo(domain: str) -> bytes | None:
    """Fetch favicon from DuckDuckGo's icon service."""
    url = f"https://icons.duckduckgo.com/ip3/{domain}.ico"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and len(response.content) > 100:
            return response.content
    except requests.RequestException as e:
        print(f"DuckDuckGo fetch failed: {e}", file=sys.stderr)
    return None


def fetch_direct(domain: str) -> bytes | None:
    """Fetch favicon directly from the website."""
    url = f"https://{domain}/favicon.ico"
    try:
        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 (compatible; FaviconFetcher/1.0)"},
        )
        if response.status_code == 200 and len(response.content) > 100:
            return response.content
    except requests.RequestException as e:
        print(f"Direct fetch failed: {e}", file=sys.stderr)
    return None


def fetch_favicon(domain: str, size: int = 128) -> tuple[bytes | None, str]:
    """
    Fetch favicon using multiple sources with fallback.
    Returns (content, extension) tuple.
    """
    # Try Google first (best quality, PNG format)
    content = fetch_from_google(domain, size)
    if content:
        return content, "png"

    # Try DuckDuckGo (privacy-focused, ICO format)
    content = fetch_from_duckduckgo(domain)
    if content:
        return content, "ico"

    # Try direct fetch (may be low quality)
    content = fetch_direct(domain)
    if content:
        return content, "ico"

    return None, ""


def main():
    parser = argparse.ArgumentParser(
        description="Fetch favicon for a domain using multiple sources"
    )
    parser.add_argument("domain", help="Domain or URL to fetch favicon for")
    parser.add_argument(
        "--size",
        type=int,
        default=128,
        choices=[16, 32, 64, 128, 256],
        help="Size hint for favicon (default: 128)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=".",
        help="Output directory (default: current directory)",
    )
    args = parser.parse_args()

    domain = extract_domain(args.domain)
    print(f"Fetching favicon for: {domain}")

    content, ext = fetch_favicon(domain, args.size)

    if not content:
        print(f"Failed to fetch favicon for {domain}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output, exist_ok=True)
    output_path = os.path.join(args.output, f"{domain}.{ext}")

    with open(output_path, "wb") as f:
        f.write(content)

    print(f"Saved: {output_path}")
    sys.exit(0)


if __name__ == "__main__":
    main()
