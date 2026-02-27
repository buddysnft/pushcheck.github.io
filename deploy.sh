#!/bin/bash

# PushCheck Website Deployment Script

echo "🚀 PushCheck Website Deployment"
echo "================================"
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial PushCheck website"
else
    echo "✅ Git repository already initialized"
fi

# Check if remote exists
if ! git remote | grep -q origin; then
    echo ""
    echo "⚠️  No git remote configured."
    echo ""
    echo "To deploy to GitHub Pages:"
    echo "1. Create a repository at: https://github.com/new"
    echo "2. Name it: pushcheck.github.io (must match exactly)"
    echo "3. Make it public"
    echo "4. Run this command:"
    echo ""
    echo "   git remote add origin https://github.com/YOUR-USERNAME/pushcheck.github.io.git"
    echo "   git branch -M main"
    echo "   git push -u origin main"
    echo ""
    echo "5. Enable GitHub Pages in repository settings:"
    echo "   Settings → Pages → Source: main branch"
    echo ""
    echo "Site will be live at: https://YOUR-USERNAME.github.io"
else
    echo "✅ Git remote configured"
    echo ""
    echo "📤 Ready to push changes?"
    echo ""
    read -p "Push to GitHub? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        git commit -m "Update PushCheck website"
        git push origin main
        echo ""
        echo "✅ Deployed! Site will update in 2-3 minutes."
        echo "   Visit: https://pushcheck.github.io"
    else
        echo "Skipped push."
    fi
fi

echo ""
echo "📊 File Summary:"
echo "  - index.html (landing page)"
echo "  - faq.html (30+ SEO questions)"
echo "  - brand-facts.html (about page)"
echo "  - .well-known/brand-facts.json (AI-readable)"
echo "  - style.css (clean, mobile-responsive)"
echo ""
echo "✅ Website ready for GitHub Pages!"
