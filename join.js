(function () {
  'use strict';
  const actions = document.getElementById('invite-actions');
  const error = document.getElementById('invite-error');
  const status = document.getElementById('invite-status');
  const title = document.getElementById('invite-title');
  const helper = window.PushCheckInvite;
  const code = helper && window.location.hash === ''
    ? helper.parseSearch(window.location.search)
    : null;
  const links = code ? helper.linksForCode(code) : null;

  if (!links) {
    title.textContent = 'Check your invitation';
    status.textContent = 'We couldn’t open this link.';
    actions.hidden = true;
    error.hidden = false;
    return;
  }

  title.textContent = 'You’re invited.';
  status.textContent = 'Tap below to join your group. No code to type.';
  document.getElementById('open-pushcheck').href = links.app;
  document.getElementById('get-pushcheck').href = links.appStore;
  actions.hidden = false;

  // No banner or outbound app URL is created until the invitation is valid.
  // Safari support for dynamically inserted banners must be device-tested.
  // The explicit Open button remains available regardless of banner behavior.
  const banner = document.createElement('meta');
  banner.name = 'apple-itunes-app';
  banner.content = links.banner;
  document.head.appendChild(banner);
})();
