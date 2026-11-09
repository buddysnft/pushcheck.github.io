# App Store website campaigns

Ordinary App Store anchors use the campaign URL format generated in App Store
Connect for PushCheck on November 9, 2026:

`https://apps.apple.com/app/apple-store/id6759138620?pt=128550277&ct=web_home&mt=8`

`pt=128550277` is the public provider token, `ct` identifies the source page,
and `mt=8` is Apple's generated media parameter. HTML escapes the query
separators as `&amp;`. The links work without JavaScript.

| Source page | Campaign (`ct`) | Links |
| --- | --- | ---: |
| `/` | `web_home` | 6 |
| `/pro.html` | `web_pro` | 4 |
| `/faq.html` | `web_faq` | 5 |
| `/brand-facts.html` | `web_brand_facts` | 7 |
| `/blog.html` | `web_blog` | 4 |
| `/blog/best-push-up-tracker-app` | `web_tracker_guide` | 3 |
| `/blog/push-up-challenge-app-for-friends` | `web_friends_guide` | 3 |
| `/guides/push-ups-apple-health.html` | `web_apple_health` | 3 |
| `/reviews.html` | `web_reviews` | 7 |
| `/404.html` | `web_404` | 2 |

These static labels identify the website page that sent someone to the App
Store. They remain the fallback when JavaScript is unavailable or no recognized
source indication exists. Read campaign performance in App Store Connect.

## Indicated AI source on the landing page

The deferred, first-party `campaign-links.js` helper can change only the 44
validated App Store link destinations above. It selects a fixed campaign from
the following source indications:

| HTTPS referrer domain, including subdomains | Explicit `utm_source` values | Campaign |
| --- | --- | --- |
| `chatgpt.com`, `chat.openai.com` | `chatgpt.com`, `chatgpt` | `ai_chatgpt` |
| `claude.ai` | `claude.ai`, `claude` | `ai_claude` |
| `perplexity.ai` | `perplexity.ai`, `perplexity` | `ai_perplexity` |

A recognized `document.referrer` takes precedence. Otherwise, exactly one
allowlisted `utm_source` value is accepted. Unknown, empty or duplicate source
markers keep the static page campaign unless the referrer is recognized.
Non-HTTPS referrers, credentials, nondefault ports and hostname lookalikes are
rejected. Explicit source values are case-sensitive.

The helper changes `ct` only on exact known PushCheck App Store URLs, preserving
the fixed app ID, provider and media parameter. It never copies raw referrer
paths, queries, inbound parameters or visitor identifiers. It adds no cookies,
browser storage, telemetry requests, redirects or cross-page state. The normal
first-party script file is loaded with the page; an App Store request still
requires the visitor to follow a link.

This is incomplete attribution of an **indicated AI source for a direct
landing-page App Store click**. Referrer suppression, disabled JavaScript or
navigating to another site page can leave only the `web_*` fallback. A person
can supply an allowlisted source marker, so it does not prove a human came from
an AI service, establish causation, or guarantee install attribution. Campaign
reporting is separate from search indexing and AI citation evidence.

Canonical URLs and structured product identity URLs remain untagged. The group
invitation flow, including its App Store link, stays separate and unchanged.
Tracking query changes do not change page publication dates or sitemap `lastmod`.

Before publishing:

```sh
python3 scripts/check_search_readiness.py
python3 scripts/check_campaign_links.py
node --test scripts/test_campaign_links.js
```

For the source helper change, verify that every page byte outside ordinary
App Store href values and the exact helper inclusion is unchanged. Protected
invitation, metadata and asset files must remain identical:

```sh
python3 scripts/check_campaign_links.py --compare-ref 47f1433
```

After publishing, run both checkers with `--live` and use `site.sh verify` for
each changed page. The campaign checker validates the app ID, provider, campaign,
media parameter, link count, ordinary anchor text, untagged search metadata,
helper inclusion and served helper content. Node tests cover source classification,
precedence, hostname spoofing, target validation and identifier leakage.
Update its mapping and counts deliberately when adding a page or App Store link.
