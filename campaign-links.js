/* Source indication for this landing page only. No storage or telemetry. */
(() => {
    'use strict';

    const STORE_URL = 'https://apps.apple.com/app/apple-store/id6759138620?pt=128550277&ct=';
    const WEB_CAMPAIGNS = [
        'web_home', 'web_pro', 'web_faq', 'web_brand_facts', 'web_blog',
        'web_tracker_guide', 'web_friends_guide', 'web_apple_health', 'web_reviews', 'web_404'
    ];
    const AI_CAMPAIGNS = new Set(['ai_chatgpt', 'ai_claude', 'ai_perplexity']);
    const WEB_LINKS = new Set(WEB_CAMPAIGNS.map((campaign) => STORE_URL + campaign + '&mt=8'));
    const REFERRERS = [
        ['chatgpt.com', 'ai_chatgpt'], ['chat.openai.com', 'ai_chatgpt'],
        ['claude.ai', 'ai_claude'], ['perplexity.ai', 'ai_perplexity']
    ];
    const SOURCE_MARKERS = new Map([
        ['chatgpt.com', 'ai_chatgpt'], ['chatgpt', 'ai_chatgpt'],
        ['claude.ai', 'ai_claude'], ['claude', 'ai_claude'],
        ['perplexity.ai', 'ai_perplexity'], ['perplexity', 'ai_perplexity']
    ]);

    function sourceCampaign(referrer, search) {
        try {
            const source = new URL(referrer);
            if (source.protocol === 'https:' && !source.username && !source.password && !source.port) {
                for (const [domain, campaign] of REFERRERS) {
                    if (source.hostname === domain || source.hostname.endsWith('.' + domain)) return campaign;
                }
            }
        } catch (_) {
            // Missing or invalid referrers leave the explicit marker as a fallback.
        }
        const markers = new URLSearchParams(search).getAll('utm_source');
        return markers.length === 1 ? SOURCE_MARKERS.get(markers[0]) || null : null;
    }

    function campaignHref(href, campaign) {
        // Exact known links validate the app ID, provider, media and query set.
        // Rebuilding from constants prevents referrer or identifier forwarding.
        return AI_CAMPAIGNS.has(campaign) && WEB_LINKS.has(href)
            ? STORE_URL + campaign + '&mt=8' : href;
    }

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { sourceCampaign, campaignHref };
    } else {
        const campaign = sourceCampaign(document.referrer, window.location.search);
        if (!campaign) return;
        document.querySelectorAll('a[href]').forEach((anchor) => {
            const href = anchor.getAttribute('href');
            const replacement = campaignHref(href, campaign);
            if (replacement !== href) anchor.setAttribute('href', replacement);
        });
    }
})();
