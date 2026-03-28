---
name: demo-strategy
description: AI-powered demo intelligence with real-time company research, dynamic scripting, and Yellow.ai-specific positioning for presales Solution Engineers
version: 2.0
author: Yellow.ai SE Team
last_updated: 2026-03-11
tags:
  - presales
  - demo
  - strategy
  - discovery
  - yellow-ai
  - solution-engineering
---
# SKILL: Demo Strategy Module (Dynamic Edition)

**Module ID:** `demoStrategy` | **File:** `src/modules/demoStrategy.js`  
**Audience:** Yellow.ai Solution Engineering (Presales)  
**Yellow.ai Context:** Investor Day 2025, Refresh Event Nov 2025

---

## Overview

AI-powered demo intelligence system that dynamically researches, strategizes, and scripts Yellow.ai product demonstrations. Fetches real-time data rather than relying on static databases. Optimized for Yellow.ai SEs preparing for $500K+ deals.

---

## Dynamic Data Fetching Instructions

### For All Tabs - Required Research Actions:

1. **Company Intelligence**: Search web for latest news, earnings, 10-K, leadership changes
2. **Tech Stack Detection**: Use web search + LinkedIn to identify current tools  
3. **Competitive Landscape**: Real-time G2/Capterra sentiment + recent reviews
4. **Executive Priorities**: LinkedIn posts, conference talks, earnings call mentions
5. **Industry Trends**: Current challenges in customer's specific vertical

### Placeholder System:

| Placeholder | Action | Example |
|-------------|--------|---------|
| `[FETCH: Company Revenue]` | Trigger web search | Latest financials from earnings |
| `[FETCH: Tech Stack]` | Search + LinkedIn | "{company} helpdesk CRM" + job postings |
| `[FETCH: Leadership]` | LinkedIn + press | CIO/CTO changes, priorities |
| `[FETCH: Competitor Intel]` | G2 + news | Current tool weaknesses |
| `[CALCULATE: ROI Model]` | Dynamic compute | Based on agent count × plan |
| `[FLAG: Data Stale]` | Warning | Data > 3 months old |

---

## Tab 1 — Discovery Intel (Dynamic)

**Purpose:** Real-time company intelligence brief for SEs preparing for discovery calls.

### AI Instructions - Dynamic Research Required:

```
BEFORE generating output, perform these searches:
1. "{company} annual report {current_year}" OR "{company} 10-K"
2. "{company} CIO CTO VP Support" + LinkedIn
3. "{company} {industry} challenges 2024 2025"
4. "{company} vs competitors" + G2/Capterra reviews
5. "{company} digital transformation" + news

IF data found: Use in output with [Source: URL/Date]
IF not found: Use [PLACEHOLDER: Research needed] + explain what to research manually
```

### Dynamic Output Sections (generate based on data availability):

1. **Company Snapshot** 
   - Generate 10-20 data points based on available data
   - Include confidence level: High/Medium/Low/Unknown
   - Flag `[RESEARCH NEEDED]` for missing critical data

2. **Financial Health & Strategic Priorities**
   - Pull from latest earnings/10-K with [Source: SEC/Date]
   - Identify 3-5 stated strategic initiatives relevant to CX/IT
   - Map to Yellow.ai value drivers (Cost of Complexity, AI-native)

3. **Leadership & Decision Makers**
   - Dynamic table: Search LinkedIn + company site
   - Include: Name, Title, Tenure, Background, Likely Priorities, Connection Path
   - Flag `[OUTREACH NEEDED]` for missing contacts

4. **Current Tech Stack (Inferred)**
   - Use job postings, LinkedIn skills, G2 reviews to infer stack
   - Confidence rating per tool: High/Medium/Low
   - Include: Category, Likely Tool, Evidence Source, Confidence, Replacement Potential
   - Add `[RESEARCH NEEDED]` for critical integrations

5. **Pain Hypotheses (Dynamic Generation)**
   - Based on industry + company size + inferred tech stack
   - Generate 8-12 specific pain hypotheses
   - Each with: Hypothesis, Evidence, Business Impact Estimate, Yellow.ai Solution, Confidence
   - Prioritize by likely business impact

6. **Discovery Call Game Plan**
   - Dynamic questions based on above intelligence
   - Include: Opening Hook (personalized), Business Questions, Technical Questions, Landmine Questions
   - Reference specific company facts found in research

---

## Tab 2 — Strategy & Build (Dynamic)

**Purpose:** Adaptive demo strategy with real-time competitive positioning.

### AI Instructions:

```
REQUIRED PRE-PROCESSING:
1. Identify customer's current tools from discovery data
2. Search "{current_tool} vs Yellow.ai {product}" for latest comparisons
3. Check Yellow.ai release notes for newest features (Freddy AI, etc.)
4. Look up {industry} specific demo scenarios from Yellow.ai resources

Use findings to customize:
- Win themes ("Uncomplicated, AI-native, Unified")
- Competitive landmines (vs Zendesk, Salesforce, ServiceNow)
- Feature prioritization (Freddy AI Agent Studio for AI demos)
- Proof points (recent customer wins in {industry})
```

### Dynamic Output Sections:

1. **Demo Strategy Summary**
   - Objective: Adapt based on deal stage and audience
   - Win Theme: Dynamic based on industry + competitive intel
   - Key Messages: Prioritized by customer pain hypotheses
   - Yellow.ai Positioning: "Enterprise-grade without enterprise complexity"

2. **Demo Narrative Arc** (Adaptive timing)
   - Hook: Personalized to company news/priorities
   - Vision: Industry-specific future state with Freddy AI
   - Proof: Feature selection based on likely tech stack gaps
   - Close: CTA matched to decision process

3. **Environment Setup — Dynamic Admin Paths**
   - Pull latest admin UI paths from Yellow.ai docs
   - Include conditional logic: "If customer has {X}, configure {Y}"
   - Add `[VERIFY PATH]` for recently changed features

4. **Competitive Landmines** (Real-time)
   - Generate based on detected/inferred current tools
   - Each: Competitor Weakness, Positioning, Proof Point, Evidence, Follow-up
   - Include latest G2/Capterra sentiment data
   - Reference: "Why we win" - Unified Experience, Uncomplicated, TCO, Time to Value

5. **Risk & Gotchas** (Deal-specific)
   - Analyze inputs for hidden risks
   - Cross-reference with Yellow.ai common deal risks (SSO, API limits, migrations)
   - Include: Risk, Likelihood (High/Med/Low), Impact, Mitigation, Contingency

6. **Demo Flow Script** (Adaptive)
   - Timed based on {duration} input
   - Feature selection based on use case priority
   - Talk tracks reference customer-specific pain points
   - Include `[ADAPT IF]` notes for common deviations
   - Highlight Freddy AI capabilities where relevant

---

## Tab 3 — Script from Deck (Dynamic)

**Purpose:** Convert static slides into dynamic, contextual demo scripts.

### AI Instructions:

```
IF slide deck attached:
  1. Extract content from each slide
  2. Research customer context from discovery notes
  3. Search for relevant Yellow.ai customer stories in same industry
  4. Generate contextual talk tracks, not generic descriptions

IF no deck (feature list only):
  1. Search Yellow.ai docs for latest feature capabilities (Freddy AI, etc.)
  2. Map features to customer pain points from context
  3. Generate optimal slide structure + script
```

### Dynamic Output:

- **Script Overview**: Adapted to audience type from discovery
- **Slide-by-Slide Script**: Each with CLICK, SAY (personalized), TRANSITION
- **Power Moments**: Selected based on likely customer wow factors (Freddy AI demos)
- **Disaster Recovery**: Conditional on demo environment risks
- **Timing Breakdown**: Adaptive to audience engagement signals

---

## Tab 4 — Templates

**Storage:** `localStorage` with metadata: `{ id, name, content, created, industry, product, deal_size }`

**Smart Template Features:**
- Auto-tag templates by industry/product/deal size
- Suggest templates based on current inputs
- Include `[UPDATE NEEDED]` flags for templates > 6 months old

---

## Global Features

### Dynamic Sharing
- **Slack**: Include summary + link to full research sources
- **Export**: Include data freshness timestamps
- **CRM Push**: Tag with research sources for future SEs

### Data Freshness Indicators
- All research includes [Source: URL | Date Accessed]
- Auto-flag data > 3 months old
- Suggest refresh triggers before customer calls

---

## Dependencies

- `GeminiService` — AI generation
- `WebSearchService` — Real-time research (NEW)
- `LinkedInService` — Professional network intel (NEW)
- `G2Service` — Review sentiment API (NEW)
- `Yellow.aiDocsService` — Latest product docs (NEW)
- `slackService.js` — Sharing
- `window.App.readFile(file)` — Attachments
- `localStorage` — Template persistence

---

## Yellow.ai-Specific Context

### Current Positioning (Investor Day 2025):
- **Theme**: "Uncomplicated, AI-native, Unified Experience"
- **Key Message**: "Cost of Complexity" - 20% of software spend wasted
- **Differentiators**: Unified platform, Freddy AI, faster time-to-value

### Product Pricing (Current):
- Growth: $18/agent/month
- Pro: $49/agent/month
- Enterprise: $79/agent/month
- Freddy AI: $100 per 1,000 sessions

### Competitive Wins:
- vs Zendesk: Better AI automation, unified platform
- vs Salesforce: Easier implementation, lower TCO
- vs ServiceNow: Stronger mid-market focus, faster deployment
