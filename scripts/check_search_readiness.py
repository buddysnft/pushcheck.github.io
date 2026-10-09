#!/usr/bin/env python3
"""Check this static site's initial HTML, metadata, schema, and robots policy.

Run locally: python3 scripts/check_search_readiness.py
Check the deployed public site: python3 scripts/check_search_readiness.py --live
Live mode makes one unauthenticated, cache-busted request per resource, without
retries. It does not prove indexing, rankings, citations, or verified bot visits.
"""

import argparse
from datetime import date, datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://pushcheck.app"
APP_ID = "6759138620"
BOTS = ("Googlebot", "Bingbot", "OAI-SearchBot", "Claude-SearchBot", "PerplexityBot")
VOID = set("area base br col embed hr img input link meta param source track wbr".split())
BLOCKED = re.compile(r"\b(?:noindex|nosnippet|none)\b|\bmax-snippet\s*:\s*0\b", re.I)


def normalized(value):
    return " ".join(value.split())


class Node:
    def __init__(self, tag="root", attrs=(), parent=None):
        self.tag, self.attrs, self.parent = tag, dict(attrs), parent
        self.children = []

    def find(self, tag=None):
        return [n for n in self.walk() if tag is None or n.tag == tag]

    def walk(self):
        for child in self.children:
            if isinstance(child, Node):
                yield child
                yield from child.walk()

    def text(self, visible=True):
        return normalized(self.raw_text(visible))

    def raw_text(self, visible=True):
        if visible and (self.tag in {"script", "style", "template", "head"}
                        or "hidden" in self.attrs or self.attrs.get("aria-hidden") == "true"):
            return ""
        text = "".join(c.raw_text(visible) if isinstance(c, Node) else c for c in self.children)
        if self.tag in {"br", "p", "div", "li", "section", "article", "h1", "h2", "h3"}:
            return "\n" + text + "\n"
        return text


class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.current = self.root
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.current)
        self.current.children.append(node)
        if tag not in VOID:
            self.current = node

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        node = self.current
        while node.parent:
            if node.tag == tag:
                self.current = node.parent
                break
            node = node.parent

    def handle_data(self, data):
        self.current.children.append(data)


def objects(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from objects(child)


class Checker:
    def __init__(self, live):
        self.live = live
        self.errors = []
        self.assets = set()
        self.stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def check(self, condition, label):
        if not condition:
            self.errors.append(label)

    def read(self, route, expected=200):
        if not self.live:
            path = ROOT / (urlsplit(route).path.lstrip("/") or "index.html")
            if not path.suffix:
                path = path.with_suffix(".html")
            return path.read_text(encoding="utf-8"), {}
        url = urljoin(BASE, route)
        url += ("&" if "?" in url else "?") + "readiness_check=" + self.stamp
        request = Request(url, headers={"User-Agent": "PushCheck-Search-Readiness/1.0",
                                        "Cache-Control": "no-cache", "Pragma": "no-cache"})
        try:
            response = urlopen(request, timeout=25)
        except HTTPError as response_error:
            response = response_error
        with response:
            self.check(response.status == expected, f"{route}: HTTP {response.status}, expected {expected}")
            self.check(urlsplit(response.url).path == urlsplit(url).path, f"{route}: unexpected redirect to {response.url}")
            return response.read().decode("utf-8"), response.headers

    def iso_date(self, value, label):
        try:
            parsed = date.fromisoformat(value[:10])
            self.check(parsed <= date.today(), f"{label}: future date {value}")
            return parsed
        except (ValueError, TypeError):
            self.check(False, f"{label}: invalid date {value!r}")
            return None

    def page(self, url, lastmod, html, headers):
        route = urlsplit(url).path
        root = Document(html).root
        titles, mains, headings = root.find("title"), root.find("main"), root.find("h1")
        self.check(len(titles) == 1 and bool(titles[0].text(False)), f"{route}: missing/duplicate title")
        self.check(len(mains) == 1, f"{route}: expected one main element")
        self.check(len(headings) == 1 and bool(headings[0].text()), f"{route}: expected one nonempty H1")
        self.check(len(mains[0].text().split()) >= 60 if mains else False,
                   f"{route}: insufficient initial HTML main text (<60 words)")
        descriptions = [n for n in root.find("meta") if n.attrs.get("name", "").lower() == "description"]
        self.check(len(descriptions) == 1 and bool(descriptions[0].attrs.get("content", "").strip()),
                   f"{route}: missing/duplicate description")
        canonicals = [n.attrs.get("href") for n in root.find("link") if "canonical" in n.attrs.get("rel", "").split()]
        self.check(canonicals == [url], f"{route}: canonical must equal sitemap URL {url}")
        directives = [n.attrs.get("content", "") for n in root.find("meta")
                      if n.attrs.get("name", "").lower() in {"robots", *(b.lower() for b in BOTS)}]
        directives.append(headers.get("X-Robots-Tag", ""))
        self.check(not any(BLOCKED.search(d) for d in directives), f"{route}: indexing or snippet restriction")
        stores = [n.attrs.get("href", "") for n in root.find("a")
                  if urlsplit(n.attrs.get("href", "")).hostname == "apps.apple.com"]
        self.check(bool(stores) and all(re.search(r"/id" + APP_ID + r"(?:[/?#]|$)", s) for s in stores),
                   f"{route}: missing or incorrect App Store destination")
        for node in root.find():
            resource_link = node.tag == "link" and bool({"stylesheet", "icon", "preload"} & set(node.attrs.get("rel", "").split()))
            target = node.attrs.get("src") or (node.attrs.get("href") if resource_link else None)
            if target:
                resolved = urlsplit(urljoin(url, target))
                if resolved.netloc == urlsplit(BASE).netloc:
                    self.assets.add(resolved.path)
        schema = []
        for node in root.find("script"):
            if node.attrs.get("type") == "application/ld+json":
                try:
                    schema.extend(objects(json.loads(node.text(False))))
                except json.JSONDecodeError as error:
                    self.check(False, f"{route}: malformed JSON-LD: {error}")
        self.check(bool(schema), f"{route}: missing JSON-LD")
        sitemap_date = self.iso_date(lastmod, f"{route} sitemap lastmod")
        page_dates = []
        for node in root.find("time"):
            machine_date = self.iso_date(node.attrs.get("datetime", ""), f"{route} visible time")
            printed_date = None
            for pattern in ("%B %d, %Y", "%b %d, %Y", "%Y-%m-%d"):
                try:
                    printed_date = datetime.strptime(node.text(), pattern).date()
                    break
                except ValueError:
                    pass
            self.check(printed_date == machine_date and machine_date is not None,
                       f"{route}: visible date text disagrees with datetime: {node.text()!r}")
            if node.parent.text().startswith("Page updated "):
                page_dates.append(node.attrs.get("datetime"))
                self.check(machine_date == sitemap_date, f"{route}: page updated date differs from sitemap lastmod")
        for item in schema:
            dates = {key: self.iso_date(item[key], f"{route} {key}")
                     for key in ("datePublished", "dateModified") if key in item}
            if all(dates.get(k) for k in ("datePublished", "dateModified")):
                self.check(dates["dateModified"] >= dates["datePublished"], f"{route}: modified before publication")
            if dates.get("dateModified") and sitemap_date:
                self.check(sitemap_date >= dates["dateModified"], f"{route}: sitemap lastmod predates content metadata")
            if item.get("@type") in ("SoftwareApplication", "FAQPage", "Blog", "WebPage", "AboutPage") and item.get("dateModified") and page_dates:
                self.check(item["dateModified"] in page_dates, f"{route}: page metadata dateModified differs from visible page updated date")
            if item.get("@type") in ("Article", "BlogPosting") and dates:
                self.article_dates(root, item, route)
        if route == "/faq.html":
            self.faq(root, schema, route)
        print(f"  Checked {route}: {len(mains[0].text().split()) if mains else 0} main words, {len(schema)} schema objects")

    def article_dates(self, root, item, route):
        heading = normalized(item.get("headline", ""))
        matches = [n for n in root.find() if n.tag in {"h1", "h2", "h3"} and n.text() == heading]
        self.check(len(matches) == 1, f"{route}: cannot match dated article headline {heading!r}")
        if len(matches) != 1:
            return
        node = matches[0]
        if node.tag == "h2":
            siblings = node.parent.children
            scope = next((s for s in siblings[siblings.index(node) + 1:] if isinstance(s, Node)), node)
        else:
            scope = node.parent
        visible_dates = [n.attrs.get("datetime") for n in scope.find("time")]
        expected = [item[k] for k in ("datePublished", "dateModified") if k in item]
        self.check(visible_dates[:len(expected)] == expected, f"{route}: dates disagree for {heading!r}: {visible_dates} vs {expected}")

    def faq(self, root, schema, route):
        visible = []
        for node in root.find():
            if "faq-item" in node.attrs.get("class", "").split():
                questions = node.find("h3")
                if questions:
                    question = questions[0].text()
                    answer = normalized(node.text()[len(question):])
                    visible.append((question, answer))
        structured = []
        for item in schema:
            if item.get("@type") == "FAQPage":
                structured.extend((normalized(q["name"]), Document(q["acceptedAnswer"]["text"]).root.text())
                                  for q in item.get("mainEntity", []))
        self.check(bool(visible) and visible == structured, f"{route}: FAQ questions/answers do not exactly match visible HTML in order")
        if visible != structured:
            for question, answer in visible:
                if (question, answer) not in structured:
                    self.errors.append(f"{route}: FAQ mismatch: {question}")

    def run(self):
        print(f"{'LIVE' if self.live else 'LOCAL'} search-readiness check at {self.stamp} (UTC)")
        sitemap, _ = self.read("/sitemap.xml")
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        entries = [(n.findtext("s:loc", namespaces=ns), n.findtext("s:lastmod", namespaces=ns))
                   for n in ET.fromstring(sitemap).findall("s:url", ns)]
        self.check(len(entries) == 6 and len({u for u, _ in entries}) == 6, "Expected six distinct sitemap pages")
        robots, _ = self.read("/robots.txt")
        policy = RobotFileParser()
        policy.parse(robots.splitlines())
        self.check(BASE + "/sitemap.xml" in (policy.site_maps() or []), "robots.txt missing sitemap")
        for url, lastmod in entries:
            if not url or urlsplit(url).netloc != urlsplit(BASE).netloc or not lastmod:
                self.check(False, f"Invalid sitemap entry: {url!r}, {lastmod!r}")
                continue
            html, headers = self.read(urlsplit(url).path)
            self.page(url, lastmod, html, headers)
        for route in {urlsplit(u).path for u, _ in entries if u} | self.assets:
            for bot in BOTS:
                self.check(policy.can_fetch(bot, urljoin(BASE, route)), f"robots.txt blocks {bot}: {route}")
            if route in self.assets and not self.live:
                self.check((ROOT / unquote(route).lstrip("/")).is_file(), f"Missing local asset {route}")
        missing_route = "/__pushcheck_readiness_missing_page__" if self.live else "/404.html"
        missing, headers = self.read(missing_route, expected=404 if self.live else 200)
        missing_doc = Document(missing).root
        noindex = [n.attrs.get("content", "") for n in missing_doc.find("meta")
                   if n.attrs.get("name", "").lower() == "robots"] + [headers.get("X-Robots-Tag", "")]
        self.check(any(re.search(r"\bnoindex\b", value, re.I) for value in noindex), "404 must retain noindex")
        print(f"  Robots policy checked for {len(BOTS)} search user agents and {len(self.assets)} linked assets.")
        print("  Policy checks and user-agent HTTP probes cannot verify genuine bot traffic or indexing.")
        if self.errors:
            print("FAIL:")
            for error in self.errors:
                print(f"  - {error}")
            return 1
        print("PASS: initial HTML and search-readiness checks passed. This is not a deployment-content diff or a ranking guarantee.")
        return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="fetch public pushcheck.app instead of local files")
    arguments = parser.parse_args()
    try:
        sys.exit(Checker(arguments.live).run())
    except (OSError, URLError, ValueError, ET.ParseError, KeyError) as error:
        print(f"ERROR: check incomplete: {error}", file=sys.stderr)
        sys.exit(1)
