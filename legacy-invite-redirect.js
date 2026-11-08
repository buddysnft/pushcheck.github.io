(function () {
  'use strict';
  const helper = window.PushCheckInvite;
  if (!helper) return;
  const code = helper.parseLegacyPath(window.location.pathname, window.location.search, window.location.hash);
  if (!code) return;
  // Web navigation only. Opening the installed app still requires a user tap.
  window.location.replace('/join.html?code=' + code);
})();
