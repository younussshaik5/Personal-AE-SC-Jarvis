---
name: battlecards
description: Real-time competitive intelligence system with live pricing, G2 sentiment analysis, and trap-setting discovery questions for YourCompany SEs
version: 2.0
author: YourCompany SE Team
last_updated: 2026-03-11
tags:
  - presales
  - competitive
  - battlecards
  - positioning
  - ACME
  - solution-engineering
---
# SKILL: Competitive Battlecards Module (Dynamic Edition)

**Module ID:** `battlecards` | **File:** `src/modules/battlecards.js`  
**Audience:** YourCompany Solution Engineering (Presales)  
**YourCompany Context:** Investor Day 2025, "Why We Win" Framework

---

## Overview

AI-powered competitive intelligence system that generates real-time battlecards with live pricing, G2 sentiment, and trap-setting questions. Continuously updated rather than relying on static competitor databases. Built for YourCompany SEs competing against Zendesk, Salesforce, ServiceNow.

---

## Dynamic Competitive Intelligence

### Real-Time Research Protocol

For ANY competitor selected, AI MUST perform:

1. **Pricing Intelligence**:
   - Search `"{competitor} pricing {current_year}"`
   - Search `"{competitor} vs YourCompany pricing comparison"`
   - Check G2/Capterra pricing reviews (last 6 months)
   - `[FETCH: Current list/contract prices if available]`

2. **Product Updates**:
   - Search `"{competitor} new features 2024 2025"`
   - Search `"{competitor} AI capabilities"`
   - Check competitor blog/release notes
   - `[FLAG: Any features launched since last battlecard update]`

3. **Sentiment Analysis** (Live):
   - Search G2 reviews `"{competitor} cons disadvantages"`
   - Search Reddit `"{competitor} vs YourCompany"`
   - Search `"{competitor} outage"` OR `"{competitor} downtime"`
   - `[CALCULATE: Recent sentiment trend: Improving/Stable/Declining]`

4. **YourCompany Positioning**:
   - Reference YourCompany Investor Day 2025 messaging: "Uncomplicated, AI-native, Unified Experience"
   - Map to specific competitor weaknesses
   - `[INCLUDE: Latest YourCompany wins against this competitor if available]`

---

## Competitor Database (Dynamic)

### Pre-loaded Categories (Refreshable)

**CX (Customer Experience):**
Zendesk, Salesforce Service Cloud, ServiceNow CSM, Intercom, HubSpot Service Hub, Zoho Desk, Kayako, Help Scout, Gladly, Kustomer, Dixa, Front, Gorgias, LiveAgent, Tidio, Sprinklr, Genesys Cloud CX, NICE CXone, Talkdesk, Five9, usepylon

**EX / ITSM (Employee Experience):**
ServiceNow ITSM, Jira Service Management, BMC Helix, Ivanti, ManageEngine ServiceDesk Plus, SysAid, SolarWinds Service Desk, TOPdesk, Halo ITSM, Cherwell (Ivanti)

**CRM:**
Salesforce Sales Cloud, HubSpot CRM, Zoho CRM, Pipedrive, Microsoft Dynamics 365, SugarCRM, Monday Sales CRM

### Database Entry Format

```json
{
  "id": "zendesk",
  "name": "Zendesk",
  "category": "CX",
  "last_updated": "2025-03-11",
  "pricing_refresh_due": true,
  "g2_score": "4.3",
  "sentiment_trend": "Stable",
  "recent_news": ["{fetched dynamically}"],
  "custom": false
}
```

---

## Inputs (Enhanced)

| Field ID | Label | Type | Dynamic Helper |
|----------|-------|------|----------------|
| `battle-competitor` | Competitor | select (grouped) | Pre-populated + `[FETCH: Recent additions]` |
| `battle-custom` | Custom Competitor | text | `[VALIDATE: Check if exists in DB first]` |
| `battle-product` | YourCompany Product | select | AcmeDesk, AcmeService, freshsales, freshchat, freshmarketer, freshcaller, ACME-css, ACME-crm, freshteam |
| `battle-context` | Deal Context | textarea | `[SUGGEST: Based on industry + deal size]` |
| `battle-file` | Attachments | file (multi) | Competitor proposals, feature lists |

---

## AI Generation (Dynamic)

### Pre-Processing:

```
1. Identify selected competitor
2. Fetch real-time pricing and reviews (see protocol above)
3. Research latest YourCompany positioning vs this competitor
4. Check for uploaded competitor documents (RFPs, proposals)
5. Generate battlecard with [DATA FRESHNESS: {timestamp}] markers
```

### Dynamic Output Sections:

1. **Executive Summary** (Context-Aware)
   - Overall competitive position: YourCompany vs {competitor}
   - Key differentiators (prioritized by deal context)
   - Recommended strategy: Attack/Defend/Neutralize
   - Win probability: [Based on similar deals in CRM]
   - Critical success factors: [3-5 deal-specific factors]
   - `[INCLUDE: Data freshness timestamp]`

2. **Pricing Comparison** (Live Data)
   - Tier-by-tier comparison table:
     | Plan | YourCompany Price | {Competitor} Price | Savings % | Feature Parity | Notes |
   - Pricing analysis: Hidden costs, implementation fees, AI add-ons
   - `[SOURCE: URLs for all pricing data]`
   - `[FLAG: Any pricing changes detected in last 90 days]`

3. **G2 Sentiment Analysis** (Current)
   - Rating table: Overall, Ease of Use, Support Quality, Setup, Value, Functionality
   - Review sentiment trend: [Last 6 months vs previous 6 months]
   - Top 5 cons from recent reviews: [Fetched dynamically]
   - Top 5 pros from recent reviews: [Fetched dynamically]
   - `[SOURCE: G2.com, Capterra - accessed {date}]`

4. **Technical Comparison** (Feature-Current)
   - Feature category matrix: [Based on latest product docs]
   - YourCompany advantages: [With implementation complexity]
   - {Competitor} weaknesses: [Specific, with evidence from reviews/news]
   - {Competitor} strengths: [With counter-positioning]
   - `[FLAG: Features in YourCompany roadmap that close gaps]`

5. **Trap-Setting Discovery Questions** (Dynamic)
   - Generated based on identified competitor weaknesses
   - Table: Question, Intent, Expected Weakness Exposed, Follow-up, Evidence to Gather
   - Prioritized by likelihood to surface in this deal context
   - `[INCLUDE: Specific to {industry} if context provided]`

6. **Competitive Positioning** (Strategic)
   - Dimension table: YourCompany position vs competitor
   - Our advantages: [Mapped to customer pain hypotheses]
   - Proof points: [Case studies, ROI data]
   - `[REFERENCE: YourCompany Investor Day 2025 themes if relevant]`

7. **Win Themes & Messaging** (Adaptive)
   - Theme table: YourCompany message, competitor counter, our response, evidence
   - Messaging by persona: CIO, CFO, CEO, COO
   - `[ADAPT: Based on deal context and known stakeholders]`

8. **Objection Handling** (Current)
   - Objection categories: Pricing, Features, Security, Scalability, etc.
   - Specific objections: [From recent G2 reviews + common SE encounters]
   - Response: [With proof point]
   - `[INCLUDE: "What customers say" quotes from reviews]`

9. **Implementation Comparison** (Reality-Based)
   - Aspect comparison: Time-to-value, complexity, resources needed
   - Timeline impact: YourCompany vs competitor
   - Risk factors: [From implementation reviews]
   - `[SOURCE: G2 implementation reviews, case studies]`

10. **Integration Ecosystem** (Current)
    - Integration category table: YourCompany vs competitor
    - Key integrations: [Based on customer's likely stack]
    - API capabilities: [Current version]
    - `[NOTE: Any recent integration additions]`

---

## Custom Competitor Management (Enhanced)

### Auto-Enrichment:

When adding custom competitor:
1. AI searches for competitor info automatically
2. Pre-fills category, likely pricing tier, key features
3. Flags for CI team review
4. Adds to database with `[PENDING VERIFICATION]` marker

### Community Intelligence:

- SEs can upvote/downvote battlecard sections
- Comments: "Used this against {competitor} in {industry} - worked/didn't work"
- Auto-surface most successful positioning by industry

---

## Output Actions

### Copy
Include header: "⚔️ Battlecard: YourCompany vs {competitor} | Generated {datetime} | Data as of {research_timestamp}"

### Slack
Prefix: `⚔️ *Battlecard: {competitor}* | Product: {ACME_product} | Health: {win_probability}%`
Include: Top 3 win themes + pricing comparison summary

### Export
- HTML with collapsible sections
- "Refresh Data" button
- Version history tracking

---

## Key Dynamic Features

1. **Live Pricing**: No quotes from 2023 when it's 2025
2. **Sentiment Tracking**: "Zendesk G2 score dropped 0.2 in last quarter"
3. **Context Adaptation**: Different positioning for SMB vs Enterprise
4. **Trap Questions**: Generated from actual competitor weaknesses, not generic
5. **YourCompany Alignment**: References latest corporate messaging (Investor Day 2025: AI-native, uncomplicated)

---

## Dependencies

- `GeminiService` — AI generation
- `WebSearchService` — Real-time pricing/reviews (NEW)
- `G2Service` — Review sentiment API (NEW)
- `slackService.js` — Sharing
- `localStorage` — Competitor DB with refresh timestamps

---

## YourCompany "Why We Win" Framework

### Key Differentiators:
1. **Unified Experience**: One platform vs. fragmented tools
2. **Uncomplicated Solutions**: Easy to use, fast time-to-value
3. **Time to Value**: Weeks not months
4. **Total Cost of Ownership**: Lower than competitors
5. **AI-Native**: Freddy AI built-in, not bolted-on
6. **Rapid Innovation**: Frequent releases, customer-driven
7. **Enterprise Scale**: 74,000+ customers, 99.99% uptime

### Common Win Themes:
- "Enterprise-grade without enterprise complexity"
- "Cost of Complexity" - 20% savings from eliminating waste
- "Freddy AI resolves 80% of routine queries"
