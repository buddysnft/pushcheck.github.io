'use strict';

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { test } = require('node:test');
const { sourceCampaign, campaignHref } = require('../campaign-links.js');

const prefix = 'https://apps.apple.com/app/apple-store/id6759138620?pt=128550277&ct=';
const store = (campaign) => prefix + campaign + '&mt=8';

test('recognizes only approved HTTPS referrer domains and their subdomains', () => {
    const sources = [
        ['chatgpt.com', 'ai_chatgpt'], ['chat.openai.com', 'ai_chatgpt'],
        ['claude.ai', 'ai_claude'], ['perplexity.ai', 'ai_perplexity']
    ];
    for (const [domain, campaign] of sources) {
        for (const host of [domain, 'www.' + domain, 'a.b.' + domain, domain.toUpperCase()]) {
            assert.equal(sourceCampaign('https://' + host + '/private?token=secret', ''), campaign);
        }
    }
});

test('rejects spoofed, unrelated, credentialed and insecure referrers', () => {
    const invalid = [
        '', 'not a URL', 'chatgpt.com', '//chatgpt.com', 'http://chatgpt.com',
        'https://evilchatgpt.com', 'https://chatgpt.com.evil.example',
        'https://chatgpt.com@evil.example', 'https://user:secret@chatgpt.com',
        'https://evil.example/?next=https://chatgpt.com', 'https://openai.com',
        'https://other.openai.com', 'https://chat.openai.com.evil.example',
        'https://evilclaude.ai', 'https://claude.ai.evil.example',
        'https://perplexity.ai.evil.example', 'https://perpIexity.ai',
        'https://chаtgpt.com', 'https://chatgpt.com:8443', 'https://chatgpt.com.'
    ];
    for (const referrer of invalid) assert.equal(sourceCampaign(referrer, ''), null, referrer);
});

test('explicit source markers use the exact allowlist and ignore unrelated parameters', () => {
    const markers = [
        ['chatgpt.com', 'ai_chatgpt'], ['chatgpt', 'ai_chatgpt'],
        ['claude.ai', 'ai_claude'], ['claude', 'ai_claude'],
        ['perplexity.ai', 'ai_perplexity'], ['perplexity', 'ai_perplexity']
    ];
    for (const [marker, campaign] of markers) {
        assert.equal(sourceCampaign('', '?email=private&client_id=secret&utm_source=' + marker), campaign);
    }
    for (const search of [
        '', '?source=chatgpt', '?UTM_SOURCE=chatgpt', '?utm_source=', '?utm_source=ChatGPT',
        '?utm_source=chatgpt.evil', '?utm_source=https%3A%2F%2Fchatgpt.com',
        '?utm_source=chatgpt%26token%3Dsecret', '?utm_source=chatgpt&utm_source=claude',
        '?utm_source=chatgpt&utm_source=chatgpt', '?utm_source=__proto__', '?utm_source=constructor'
    ]) assert.equal(sourceCampaign('', search), null, search);
});

test('recognized referrer takes precedence; unknown referrer permits a valid marker', () => {
    assert.equal(sourceCampaign('https://chatgpt.com/', '?utm_source=claude'), 'ai_chatgpt');
    assert.equal(sourceCampaign('https://claude.ai/', '?utm_source=unknown'), 'ai_claude');
    assert.equal(sourceCampaign('https://perplexity.ai/', '?utm_source=chatgpt&utm_source=claude'), 'ai_perplexity');
    assert.equal(sourceCampaign('https://example.com/', '?utm_source=claude'), 'ai_claude');
    assert.equal(sourceCampaign('invalid', '?utm_source=perplexity'), 'ai_perplexity');
});

test('changes only exact previously validated static PushCheck campaign links', () => {
    for (const campaign of [
        'web_home', 'web_pro', 'web_faq', 'web_brand_facts', 'web_blog',
        'web_tracker_guide', 'web_friends_guide', 'web_apple_health', 'web_reviews', 'web_404'
    ]) {
        for (const ai of ['ai_chatgpt', 'ai_claude', 'ai_perplexity']) {
            assert.equal(campaignHref(store(campaign), ai), store(ai));
        }
    }
    const invalid = [
        store('web_unknown'), store('ai_chatgpt'), store('web_home') + '&email=private',
        store('web_home') + '&ct=web_home', store('web_home') + '#private',
        store('web_home').replace('6759138620', '1234567890'),
        store('web_home').replace('128550277', '000000000'),
        store('web_home').replace('mt=8', 'mt=1'),
        store('web_home').replace('https:', 'http:'),
        store('web_home').replace('apps.apple.com', 'apps.apple.com.evil.example'),
        store('web_home').replace('apps.apple.com', 'user@' + 'apps.apple.com'),
        store('web_home').replace('/app/apple-store/', '/app/other/'),
        'https://apps.apple.com/app/id6759138620', '/join.html?invite=private', '', null
    ];
    for (const href of invalid) assert.equal(campaignHref(href, 'ai_chatgpt'), href);
    for (const campaign of [null, '', 'web_home', 'ai_unknown', 'ai_chatgpt&email=private']) {
        assert.equal(campaignHref(store('web_home'), campaign), store('web_home'));
    }
});

test('output contains only fixed app, provider, campaign and media values', () => {
    const campaign = sourceCampaign('https://claude.ai/private-conversation?token=secret',
        '?utm_source=chatgpt&email=private@example.com&user_id=secret&ct=attack&pt=attack');
    const output = campaignHref(store('web_home'), campaign);
    assert.equal(output, store('ai_claude'));
    assert.deepEqual([...new URL(output).searchParams], [
        ['pt', '128550277'], ['ct', 'ai_claude'], ['mt', '8']
    ]);
});

test('browser integration changes hrefs only, adds no state, and is idempotent', () => {
    const source = fs.readFileSync(path.join(__dirname, '../campaign-links.js'), 'utf8');
    const attributes = [
        { href: store('web_home'), class: 'cta-button', title: 'Download' },
        { href: '/pro.html', class: 'text-link' },
        { href: 'https://apps.apple.com/app/id6759138620', id: 'get-pushcheck' }
    ];
    const before = structuredClone(attributes);
    const context = {
        URL, URLSearchParams,
        document: {
            referrer: 'https://chatgpt.com/private?user_id=secret',
            querySelectorAll(selector) {
                assert.equal(selector, 'a[href]');
                return attributes.map((attrs) => ({
                    getAttribute: (name) => attrs[name],
                    setAttribute(name, value) { assert.equal(name, 'href'); attrs[name] = value; }
                }));
            }
        },
        window: { location: { search: '?utm_source=claude&email=private' } }
    };
    for (const target of [context, context.window, context.document]) {
        for (const name of ['cookie', 'localStorage', 'sessionStorage', 'fetch', 'XMLHttpRequest', 'navigator']) {
            Object.defineProperty(target, name, { get() { throw new Error('Forbidden access: ' + name); } });
        }
    }
    vm.runInNewContext(source, context);
    vm.runInNewContext(source, context);
    assert.deepEqual(attributes, [{ ...before[0], href: store('ai_chatgpt') }, before[1], before[2]]);
    assert.equal(context.window.location.search, '?utm_source=claude&email=private');

    context.document.referrer = 'https://pushcheck.app/';
    context.window.location.search = '';
    context.document.querySelectorAll = () => { throw new Error('Unknown source must leave links untouched'); };
    vm.runInNewContext(source, context);
});
