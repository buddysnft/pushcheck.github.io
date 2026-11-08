(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.PushCheckInvite = api;
})(typeof globalThis === 'object' ? globalThis : this, function () {
  'use strict';

  const origin = 'https://pushcheck.app';
  const appStoreURL = 'https://apps.apple.com/app/id6759138620';
  // Compatibility only: these values are ignored, never stored or transmitted.
  const trackingNames = new Set(['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'utm_id', 'source', 'ref']);

  function normalizeCode(value) {
    return typeof value === 'string' && /^[A-Za-z0-9]{6}$/.test(value)
      ? value.toUpperCase()
      : null;
  }

  // A shared invitation has one code parameter. Reject ambiguous or malformed
  // input instead of silently selecting a different invitation.
  function parseSearch(search) {
    if (typeof search !== 'string' || !search.startsWith('?')) return null;
    const entries = queryEntries(search);
    if (!entries || entries.some(([name]) => name !== 'code' && !trackingNames.has(name))) return null;
    const codes = entries.filter(([name]) => name === 'code');
    return codes.length === 1 ? normalizeCode(codes[0][1]) : null;
  }

  function parseLegacyPath(pathname, search, hash) {
    if (typeof pathname !== 'string' || hash !== '') return null;
    const entries = queryEntries(search);
    if (!entries || entries.some(([name]) => !trackingNames.has(name))) return null;
    const match = /^\/join\/([A-Za-z0-9]{6})\/?$/.exec(pathname);
    return match ? normalizeCode(match[1]) : null;
  }

  function queryEntries(search) {
    if (typeof search !== 'string' || (search !== '' && !search.startsWith('?')) || search.includes('#')) return null;
    if (/%(?![0-9a-fA-F]{2})/.test(search)) return null;
    return Array.from(new URLSearchParams(search).entries());
  }

  function linksForCode(value) {
    const code = normalizeCode(value);
    if (!code) return null;
    return Object.freeze({
      web: origin + '/join.html?code=' + code,
      app: 'pushcheck://join/' + code,
      appStore: appStoreURL,
      banner: 'app-id=6759138620, app-argument=pushcheck://join/' + code
    });
  }

  return Object.freeze({ normalizeCode, parseSearch, parseLegacyPath, linksForCode });
});
