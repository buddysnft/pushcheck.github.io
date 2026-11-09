#!/usr/bin/env python3
"""Validate ordinary App Store anchors and optional href-only baseline parity.

Use --live after deployment. Use --compare-ref REF locally to prove that the
campaign edit preserves page bytes outside App Store hrefs and invitation files.
"""

import argparse
from html import unescape
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import URLError
from urllib.parse import parse_qs, urlsplit

from check_search_readiness import Checker, Document

ROOT = Path(__file__).resolve().parents[1]
APP_ID = "6759138620"
PROVIDER = "128550277"
CAMPAIGNS = {
    "index.html": ("web_home", 6),
    "pro.html": ("web_pro", 4),
    "faq.html": ("web_faq", 5),
    "brand-facts.html": ("web_brand_facts", 7),
    "blog.html": ("web_blog", 4),
    "blog/best-push-up-tracker-app.html": ("web_tracker_guide", 3),
    "blog/push-up-challenge-app-for-friends.html": ("web_friends_guide", 3),
    "guides/push-ups-apple-health.html": ("web_apple_health", 3),
    "reviews.html": ("web_reviews", 7),
    "404.html": ("web_404", 2),
}
PRESERVED = (
    "join.html", "join.js", "invite-link.js", "legacy-invite-redirect.js",
    ".well-known/apple-app-site-association", ".well-known/brand-facts.json",
    "sitemap.xml", "robots.txt", "navigation.js", "style.css",
)
ANCHOR_HREF = re.compile(r'(<a\b[^>]*?\bhref\s*=\s*)([\"\x27])(.*?)(\2)', re.I | re.S)


def campaign_url(campaign):
    return f"https://apps.apple.com/app/apple-store/id{APP_ID}?pt={PROVIDER}&ct={campaign}&mt=8"


def mask_store_hrefs(html):
    """Mask only ordinary App Store href values, preserving all other bytes."""
    def replace(match):
        if urlsplit(unescape(match[3])).hostname == "apps.apple.com":
            return match[1] + match[2] + "APP_STORE_HREF" + match[4]
        return match[0]
    return ANCHOR_HREF.sub(replace, html)


def baseline(ref, path):
    return subprocess.check_output(
        ["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True, encoding="utf-8"
    )


def run(live=False, compare_ref=None):
    checker = Checker(live)
    total = 0
    print(f"{'LIVE' if live else 'LOCAL'} App Store campaign link check")
    for path, (campaign, expected_count) in CAMPAIGNS.items():
        route = "/" if path == "index.html" else "/" + path
        if path.startswith("blog/"):
            route = route.removesuffix(".html")
        html, _ = checker.read(route)
        document = Document(html).root
        anchors = [node for node in document.find("a")
                   if urlsplit(node.attrs.get("href", "")).hostname == "apps.apple.com"]
        checker.check(re.fullmatch(r"web_[a-z0-9_]+", campaign) and len(campaign) <= 30,
                      f"{path}: invalid campaign name")
        checker.check(len(anchors) == expected_count,
                      f"{path}: expected {expected_count} ordinary App Store anchors, found {len(anchors)}")
        for anchor in anchors:
            href = anchor.attrs["href"]
            parsed = urlsplit(href)
            checker.check(parsed.scheme == "https" and parsed.path == f"/app/apple-store/id{APP_ID}"
                          and not parsed.fragment and parsed.netloc == "apps.apple.com",
                          f"{path}: incorrect App Store destination: {href}")
            checker.check(parse_qs(parsed.query, keep_blank_values=True) ==
                          {"pt": [PROVIDER], "ct": [campaign], "mt": ["8"]},
                          f"{path}: incorrect campaign parameters: {href}")
            checker.check(href == campaign_url(campaign), f"{path}: unexpected campaign URL format")
            checker.check(bool(anchor.text()), f"{path}: empty App Store anchor")
            checker.check(not any(key.startswith("on") for key in anchor.attrs),
                          f"{path}: App Store anchor has a JavaScript event handler")
        for node in document.find():
            if node.tag == "link" and "canonical" in node.attrs.get("rel", "").split():
                checker.check(not urlsplit(node.attrs.get("href", "")).query,
                              f"{path}: campaign parameters added to canonical URL")
            if node.tag == "script" and node.attrs.get("type") == "application/ld+json":
                checker.check(not re.search(r"[?&](?:pt|ct|mt)=", node.text(False)),
                              f"{path}: campaign parameters added to structured data")
        if compare_ref:
            previous = baseline(compare_ref, path)
            checker.check(mask_store_hrefs(previous) == mask_store_hrefs(html),
                          f"{path}: content changed outside ordinary App Store href values")
        total += len(anchors)
        print(f"  {path}: {campaign}, {len(anchors)} anchors")
    if not live:
        for path in ROOT.rglob("*.html"):
            relative = path.relative_to(ROOT).as_posix()
            if relative in CAMPAIGNS or relative == "join.html":
                continue
            anchors = Document(path.read_text(encoding="utf-8")).root.find("a")
            checker.check(not any(urlsplit(n.attrs.get("href", "")).hostname == "apps.apple.com"
                                  for n in anchors), f"{relative}: App Store links need a campaign mapping")
    if compare_ref:
        for path in PRESERVED:
            checker.check(baseline(compare_ref, path) == (ROOT / path).read_text(encoding="utf-8"),
                          f"{path}: protected file changed from {compare_ref}")
        print(f"  Baseline {compare_ref}: page bytes outside hrefs and {len(PRESERVED)} protected files checked.")
    if checker.errors:
        print("FAIL:\n" + "\n".join("  - " + error for error in checker.errors))
        return 1
    print(f"PASS: {total} ordinary App Store anchors across {len(CAMPAIGNS)} pages.")
    print("Campaign labels identify website origin; they do not establish AI referrals or conversions.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="check deployed pages with cache-busted requests")
    parser.add_argument("--compare-ref", help="local Git ref before the campaign edit")
    args = parser.parse_args()
    if args.live and args.compare_ref:
        parser.error("--compare-ref is a local-only check")
    try:
        sys.exit(run(args.live, args.compare_ref))
    except (OSError, URLError, ValueError, subprocess.CalledProcessError) as error:
        print(f"ERROR: check incomplete: {error}", file=sys.stderr)
        sys.exit(1)
