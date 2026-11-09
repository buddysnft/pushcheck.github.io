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

These labels identify the website page that sent someone to the App Store.
They do not identify an AI referral or prove that a visitor installed the app.
Read campaign performance in App Store Connect; the website adds no analytics
scripts, cookies, or visitor identifiers. Campaign reporting is separate from
search indexing and AI citation evidence.

Canonical URLs and structured product identity URLs remain untagged. The group
invitation flow, including its App Store link, stays separate and unchanged.
Tracking query changes do not change page publication dates or sitemap `lastmod`.

Before publishing:

```sh
python3 scripts/check_search_readiness.py
python3 scripts/check_campaign_links.py
```

For the initial campaign change, verify that every page byte outside ordinary
App Store href values and the protected invitation/assets files is unchanged:

```sh
python3 scripts/check_campaign_links.py --compare-ref f748a07
```

After publishing, run both checkers with `--live` and use `site.sh verify` for
each changed page. The campaign checker validates the app ID, provider, campaign,
media parameter, link count, ordinary anchor text, and untagged search metadata.
Update its mapping and counts deliberately when adding a page or App Store link.
