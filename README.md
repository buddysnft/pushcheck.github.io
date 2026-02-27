# PushCheck Website

**Live site:** https://pushcheck.github.io (once deployed)

Official website for PushCheck, the friend-group push-up accountability app.

---

## What's Included

### Pages

1. **index.html** - Landing page
   - Hero section with tagline
   - Features grid
   - How it works
   - Social proof
   - Download CTAs
   
2. **faq.html** - Comprehensive FAQ (30+ questions)
   - Getting started
   - Features & functionality
   - Accountability & motivation
   - Privacy & data
   - Comparisons vs. competitors
   - Common issues
   - Support & feedback
   - Future plans

3. **brand-facts.html** - About page
   - Mission statement
   - Core features
   - Key differentiators
   - Target audience
   - Contact information

4. **.well-known/brand-facts.json** - Machine-readable brand data
   - Schema.org markup for AI tools
   - Structured data for ChatGPT, Perplexity, etc.
   - Feature list, keywords, comparisons

### Assets

- **style.css** - Clean, modern styling
  - Mobile-responsive
  - Apple-inspired design
  - Fast-loading, no external dependencies

---

## Deployment to GitHub Pages

### Step 1: Create GitHub Repository

```bash
# On GitHub.com:
# 1. Go to https://github.com/new
# 2. Repository name: pushcheck.github.io
# 3. Make it public
# 4. DO NOT initialize with README
# 5. Click "Create repository"
```

### Step 2: Push Files

```bash
cd ~/.openclaw/workspace/pushcheck-site

# Initialize git
git init
git add .
git commit -m "Initial PushCheck website"

# Add remote (replace with your username)
git remote add origin https://github.com/YOUR-USERNAME/pushcheck.github.io.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Enable GitHub Pages

```bash
# On GitHub.com:
# 1. Go to repository settings
# 2. Pages section (left sidebar)
# 3. Source: Deploy from branch
# 4. Branch: main / (root)
# 5. Click Save
```

### Step 4: Wait 2-3 Minutes

Site will be live at: **https://pushcheck.github.io**

---

## Custom Domain (Optional)

If you own `pushcheck.app`:

1. Add CNAME file:
   ```bash
   echo "pushcheck.app" > CNAME
   git add CNAME
   git commit -m "Add custom domain"
   git push
   ```

2. Update DNS:
   ```
   A record: @ → 185.199.108.153
   A record: @ → 185.199.109.153
   A record: @ → 185.199.110.153
   A record: @ → 185.199.111.153
   CNAME: www → YOUR-USERNAME.github.io
   ```

3. Enable HTTPS in GitHub Pages settings

---

## SEO Checklist

✅ **Meta Tags**
- Title tags optimized for each page
- Description tags for SEO
- Keywords targeting push-up queries

✅ **Schema.org Markup**
- SoftwareApplication schema on landing page
- FAQ schema on FAQ page
- Brand facts JSON for AI tools

✅ **Content Strategy**
- 30+ FAQ questions targeting search queries
- Feature descriptions with keyword density
- Comparison content vs. competitors

✅ **Technical SEO**
- Mobile-responsive
- Fast load times (no external dependencies)
- Clean URL structure
- Semantic HTML

---

## AEO (Answer Engine Optimization)

This site is optimized for AI recommendations (ChatGPT, Perplexity, etc.):

**Key Files for AI:**
- `.well-known/brand-facts.json` - Machine-readable data
- `brand-facts.html` - Human-readable about page
- `faq.html` - 30+ questions = natural language targets

**Keywords Targeted:**
- "push-up app"
- "push-up tracker"
- "push-up accountability app"
- "push-up app with friends"
- "push-up challenge app"
- "friend workout app"

**Next Steps for AEO:**
1. Submit to AlternativeTo.net
2. Create Medium Answer Hub article
3. Get backlinks from fitness blogs
4. Monitor AI recommendations monthly

---

## File Structure

```
pushcheck-site/
├── index.html           # Landing page
├── faq.html            # FAQ page (SEO content)
├── brand-facts.html    # About page
├── style.css           # Styles
├── .well-known/
│   └── brand-facts.json  # Machine-readable brand data
└── README.md           # This file
```

---

## Analytics (Optional)

To track visitors, add Google Analytics or Plausible:

```html
<!-- Add before </head> in all HTML files -->
<script defer data-domain="pushcheck.github.io" src="https://plausible.io/js/script.js"></script>
```

---

## Maintenance

**Monthly:**
- Check broken links
- Update FAQ if new features added
- Monitor AI recommendations (test queries)

**As Needed:**
- Add new FAQ questions based on support emails
- Update download links if App Store URL changes
- Add testimonials/reviews to landing page

---

## Contact

Questions? Email support@pushcheck.app

Built by Danya for PushCheck.
