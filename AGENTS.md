# AGENTS.md — pushcheck-site

Static site for PushCheck. Live at **https://pushcheck.app** via GitHub Pages
(repo `buddysnft/pushcheck.github.io`, branch `main`, custom domain in `CNAME`).

There is **exactly one** clone of this repo on this machine:
`/Users/jonbot/projects/pushcheck-site`. Edits made anywhere else are lost.

---

## The two hard rules

### 1. Pull before editing. Every time.

```bash
cd /Users/jonbot/projects/pushcheck-site && ./site.sh preflight
```

Never open a file in this repo before that command passes. This checkout has gone
stale before and it will again, because commits reach `origin` from sessions that
do not run on this checkout.

Editing a stale tree is not a cosmetic problem. Writing a file whose base is
11 commits old and pushing it **reverts live content** and produces a "done"
report describing files that were never deployed.

### 2. Verify the live URL before reporting done.

```bash
./site.sh verify "some exact string from the change you just made"
./site.sh verify "some exact string" index.html   # non-default page
```

Rules for verification:

- Verify the **live https://pushcheck.app URL**, not the local file, not the
  GitHub blob view, not `git show`. A successful push is not proof of a
  successful deploy.
- Always cache-bust. `site.sh` does this; if going manual, use
  `curl -H 'Cache-Control: no-cache' "https://pushcheck.app/faq.html?cb=$RANDOM"`.
- Pages rebuilds take roughly 1 to 3 minutes. Poll, do not assume.
- Grep for a string **unique to this change**. Not a word that already existed
  on the page, which passes trivially and proves nothing.
- Verify every page you touched, not just one.
- If verification fails, say so plainly. Never report "pushed and live" on an
  unverified or failed check.

`./site.sh status` shows drift plus HTTP status for all pages.

---

## Content rules

- **No em dashes or en dashes.** Anywhere. Use a comma, colon, or new sentence.
  Sweep before commit: `grep -rn "—\|–" *.html *.xml`
- **No invented quotes, statistics, testimonials, features, or ratings.** If it
  is not confirmed shipped in the app, it does not go on the site. Fake
  testimonials were removed once already; do not reintroduce that pattern.
- Keep the existing voice: direct, dry, second person, no hype, no exclamation
  marks. Read neighboring copy before writing new copy.
- Keep the dark theme. All styling lives in `style.css`; do not add inline
  styles or new color values.

## Structured data

Several pages carry JSON-LD that **must stay in sync with the visible HTML**:

| File | Schema | Sync requirement |
|---|---|---|
| `faq.html` | `FAQPage` | Every visible `<h3>` Q and its answer mirrored in `mainEntity`, exact 1:1 |
| `blog.html` | `Blog` | Every post has a `blogPost` entry with matching `datePublished` |
| `index.html` | `SoftwareApplication` | Pricing/offer claims match the FAQ |

After editing schema, prove it parses and that parity holds:

```bash
python3 -c "
import json,re
h=open('faq.html').read()
d=json.loads(re.search(r'<script type=\"application/ld\+json\">(.*?)</script>',h,re.S).group(1))
names=[q['name'] for q in d['mainEntity']]
h3=[re.sub(r'<[^>]+>','',x) for x in re.findall(r'<h3>(.*?)</h3>',h)]
print('schema:',len(names),'html:',len(h3))
print('missing from HTML:',[n for n in names if n not in h3])
print('missing from schema:',[x for x in h3 if x not in names])
"
```

## Pages that also carry product claims

Easy to miss when updating a feature or price. Sweep all of these:

- `index.html` — feature grid, How It Works, footer CTA text
- `faq.html` — pricing answers, Pro answers, "will it stay free", group answers
- `blog.html` — release posts, plus older posts that may now be stale
- `blog/*.html` — long-form SEO articles contain pricing and feature language
- `brand-facts.html` — press/LLM-facing facts, **and** `.well-known/brand-facts.json`
- `sitemap.xml` — bump `lastmod` on every page touched

When a Pro or pricing detail changes, `grep -rn "6.99\|subscription\|Pro\b" *.html blog/ .well-known/`
and fix every hit. Do not fix only the file named in the request.

## Do not

- Do not use `deploy.sh` for content updates. It does `git add .` with a generic
  message and no pull. Commit deliberately by hand.
- Do not `rm`. Use `trash`.
- Do not force push. Do not rewrite published history.
