#!/bin/bash
# PushCheck site workflow guard.
#
# Two standing rules, enforced here so they cannot be skipped from memory:
#   1. ALWAYS sync before editing.   ./site.sh preflight
#   2. ALWAYS verify live after push. ./site.sh verify "<string that must be served>"
#
# Why this exists: on 2026-07-28 this checkout was found 11 commits behind origin
# (last local commit 2026-05-10, origin had moved through 2026-07-19). Editing a
# stale tree risks reverting live content and reporting success on files that were
# never actually the deployed versions.

set -uo pipefail
cd "$(dirname "$0")" || exit 1

LIVE="https://pushcheck.app"
PAGES=(index.html faq.html blog.html brand-facts.html sitemap.xml)

fail() { echo "❌ $*" >&2; exit 1; }
ok()   { echo "✅ $*"; }

preflight() {
  echo "🔄 Preflight: sync before editing"
  echo "================================="

  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not a git repo"

  if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Working tree is dirty:"
    git status --short
    fail "Commit, stash, or discard local changes before syncing. Refusing to touch uncommitted work."
  fi
  ok "working tree clean"

  git fetch origin --quiet || fail "git fetch failed (check network/auth)"

  local behind ahead
  behind=$(git rev-list --count HEAD..origin/main)
  ahead=$(git rev-list --count origin/main..HEAD)

  if [ "$behind" -gt 0 ]; then
    echo "⚠️  Local is $behind commit(s) BEHIND origin/main. Fast-forwarding."
    git merge --ff-only origin/main || fail "fast-forward failed; resolve manually. DO NOT edit yet."
    ok "fast-forwarded to $(git rev-parse --short HEAD)"
  else
    ok "up to date with origin/main"
  fi

  [ "$ahead" -gt 0 ] && echo "ℹ️  $ahead local commit(s) not yet pushed."

  echo ""
  echo "HEAD: $(git log -1 --format='%h %ad %s' --date=short)"
  echo "✅ Safe to edit."
}

verify() {
  local needle="${1:-}"
  [ -z "$needle" ] && fail "usage: ./site.sh verify \"<string that must appear live>\" [page]"
  local page="${2:-faq.html}"

  echo "🔍 Verifying live: $LIVE/$page"
  echo "==================================="
  echo "Looking for: $needle"
  echo ""

  local local_head remote_head
  local_head=$(git rev-parse HEAD)
  git fetch origin --quiet 2>/dev/null
  remote_head=$(git rev-parse origin/main 2>/dev/null)
  if [ "$local_head" != "$remote_head" ]; then
    echo "⚠️  HEAD ($(git rev-parse --short HEAD)) != origin/main. Push before verifying."
  fi

  # GitHub Pages rebuild is not instant. Poll, cache-busted, up to ~5 min.
  local i body
  for i in $(seq 1 10); do
    body=$(curl -fsS -H 'Cache-Control: no-cache' -H 'Pragma: no-cache' \
             "$LIVE/$page?cb=$RANDOM$$" 2>/dev/null)
    if printf '%s' "$body" | grep -qF -- "$needle"; then
      ok "CONFIRMED LIVE on attempt $i"
      echo ""
      echo "Serving:"
      printf '%s' "$body" | grep -oF -- "$needle" | head -1
      return 0
    fi
    echo "   attempt $i: not served yet, waiting 30s..."
    sleep 30
  done

  fail "String NOT served after ~5 min. DO NOT report 'pushed and live'. Check the push, the Pages build, and the string."
}

status() {
  echo "📊 Live vs local"
  echo "================"
  git fetch origin --quiet 2>/dev/null
  echo "local HEAD:  $(git rev-parse --short HEAD)  $(git log -1 --format='%ad' --date=short)"
  echo "origin/main: $(git rev-parse --short origin/main)"
  echo "behind: $(git rev-list --count HEAD..origin/main)  ahead: $(git rev-list --count origin/main..HEAD)"
  echo ""
  for p in "${PAGES[@]}"; do
    printf '  %-18s HTTP %s\n' "$p" \
      "$(curl -o /dev/null -sw '%{http_code}' "$LIVE/$p?cb=$RANDOM")"
  done
}

case "${1:-}" in
  preflight) preflight ;;
  verify)    shift; verify "$@" ;;
  status)    status ;;
  *)
    cat <<'USAGE'
PushCheck site workflow guard.

  ./site.sh preflight
      Run BEFORE any edit. Refuses to proceed on a dirty tree,
      fetches, and fast-forwards if behind origin/main.

  ./site.sh verify "<string>" [page]
      Run AFTER pushing. Polls the live URL cache-busted for up to
      ~5 min. Exits non-zero if the string is not actually served.
      Default page: faq.html

  ./site.sh status
      Show local vs origin drift and HTTP status of every page.

Standing rule: pull before editing, verify live before reporting done.
USAGE
    exit 1 ;;
esac
