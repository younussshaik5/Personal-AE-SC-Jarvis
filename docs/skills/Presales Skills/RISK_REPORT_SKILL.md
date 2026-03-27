---
name: risk-report
description: Dynamic deal risk assessment with real-time market intelligence, stakeholder research, and YourCompany-specific risk patterns for Solution Engineers
version: 2.0
author: YourCompany SE Team
last_updated: 2026-03-11
tags:
  - presales
  - risk
  - assessment
  - deal-qualification
  - freshworks
  - solution-engineering
---
# SKILL: Risk Report Module (Dynamic Edition)

**Module ID:** `riskReport` | **File:** `src/modules/riskReport.js`  
**Audience:** YourCompany Solution Engineering (Presales)  
**YourCompany Context:** Investor Day 2025, Common Deal Risks

---

## Overview

AI-powered deal risk assessment with real-time market intelligence. Combines pattern detection with dynamic external research for comprehensive technical risk evaluation. Optimized for YourCompany enterprise deals.

---

## Dynamic Risk Intelligence System

### Real-Time Research Triggers

When generating report, AI MUST perform these searches:

1. **Company Risk Signals**: 
   - `"{customer} layoffs"` OR `"{customer} budget freeze"` OR `"{customer} merger"`
   - `"{customer} earnings Q{current_quarter}"`

2. **Industry Headwinds**: 
   - `"{industry} spending cuts 2024 2025"` 
   - `"{industry} recession impact"`

3. **Tech Stack Risks**: 
   - `"{inferred_current_tool} data breach"` 
   - `"{inferred_current_tool} outage"`

4. **Competitive Moves**: 
   - `"{competitor} price cut"` 
   - `"{competitor} new feature {use_case}"`

5. **YourCompany Specific**: 
   - Check YourCompany status page for service issues in customer's region

### Dynamic Risk Categories (Adaptive)

Instead of static 10 patterns, use these dynamic detection areas:

**Technical Risks (Auto-detect + Research):**
- `[FETCH: SSO/Security requirements]` → Search "{company} cybersecurity requirements"
- `[FETCH: Data migration complexity]` → Search "{current_tool} to YourCompany migration"
- `[FETCH: Integration requirements]` → Search "{company} tech stack integrations"
- `[FETCH: Compliance needs]` → Search "{industry} compliance requirements HIPAA SOC2"

**Business Risks (Real-time):**
- `[FETCH: Budget authority]` → Search "{company} IT budget 2024 2025"
- `[FETCH: Decision timeline]` → Search "{company} fiscal year end" OR "{company} planning cycle"
- `[FETCH: Stakeholder changes]` → Search "{company} CIO CTO VP" + "joined" OR "left"

**Competitive Risks (Live Intel):**
- `[FETCH: Competitor activity]` → Search "{competitor} {product} pricing"
- `[FETCH: Market positioning]` → G2 comparison "YourCompany vs {competitor} {industry}"

---

## Inputs (Enhanced with Dynamic Context)

| Field ID | Label | Type | Dynamic Helper |
|----------|-------|------|----------------|
| `risk-initials` | SE Initials | text | Auto-populate from user profile |
| `risk-customer` | Customer / Deal Name | text | `[FETCH: Suggest from CRM open deals]` |
| `risk-stage` | Deal Stage | select | discovery, technical-eval, poc, proposal, negotiation |
| `risk-revenue` | Estimated Revenue (ARR) | text | `[CALCULATE: Auto-calc from agent count × plan]` |
| `risk-usecases` | Use Cases Identified | textarea | `[SUGGEST: Based on industry + product]` |
| `risk-steps` | Steps Taken (SE Activities) | textarea | `[FETCH: Auto-log from CRM activities]` |
| `risk-gaps` | Known Gaps / Blockers | textarea | `[AUTO-DETECT: From use case text + research]` |
| `risk-partner` | Partner Activity | textarea | `[FETCH: Partner portal status]` |
| `risk-display-file` | Attachments | file (multi) | Architecture diagrams, RFPs |

---

## AI Generation (Dynamic)

### Pre-Processing Instructions:

```
1. Analyze all input text for risk signals
2. Perform web searches for external risk context (see above)
3. Cross-reference with YourCompany common deal risks database
4. Check similar past deals in CRM for pattern matching
5. Generate risk severity based on: Probability × Impact × Timeliness
```

### Dynamic Output Format (Adaptive Structure):

Instead of fixed "no tables" rule, use format best suited to risk type:

1. **Executive Risk Summary** 
   - Deal Health Score: X/100 (dynamic calculation)
   - Risk Level: 🔴 High / 🟡 Medium / 🟢 Low (with explanation)
   - Top 3 Risks Requiring Immediate Action (prioritized by business impact)

2. **Technical Use Cases & Solutions**
   - Dynamic list based on `risk-usecases` + industry research
   - Each: Use Case → YourCompany Solution → Implementation Risk → Mitigation

3. **SE Activity Log** (Auto-enhanced)
   - Quantify: "(3) Discovery calls, (2) Demos, (1) POC session"
   - `[FETCH: Add CRM activity timestamps if available]`

4. **Stakeholder Map** (Dynamic Research)
   - Who we've met: [From input]
   - Who we need to meet: [SUGGEST: Based on deal size + industry standards]
   - `[FETCH: LinkedIn research for key decision makers not yet engaged]`

5. **Outstanding Items & Next Steps**
   - Technical perspective with owners and due dates
   - `[FLAG: Items blocking progression to next stage]`

6. **Technical Gaps / Risks** (Categorized)
   - **Confirmed Gaps**: From `risk-gaps` input
   - **Inferred Gaps**: From pattern detection + research
   - **External Risks**: From real-time research [Source: URL]
   - Each: Gap, Evidence, Business Impact, YourCompany Capability, Workaround, Confidence

7. **Partner & Ecosystem Risks**
   - Current partner status + any external research on partner performance

8. **Risk Trend Analysis** (NEW)
   - `[FETCH: Compare to similar deals at same stage - win/loss patterns]`
   - Risk trajectory: Improving / Stable / Worsening

---

## Auto-Detect Risks (Enhanced)

### Dynamic Pattern Engine:

Instead of static regex, use AI + web search combo:

1. **Text Analysis**: AI identifies risk signals in input text
2. **Web Corroboration**: Search validates/inflates risk signals
3. **Severity Scoring**: Based on YourCompany historical deal data

**Example Dynamic Detection:**
- Input mentions "legacy system" → Search "{legacy_system} end of life" → If found, elevate to HIGH severity
- Input mentions "budget" → Search "{company} budget cuts" → If news found, add external validation

---

## Export / Sharing

### Copy
Include data freshness timestamp: "Report generated {datetime} | Research current as of {search_time}"

### Slack
Prefix: `⚠️ *Risk Report: {customer}* | Health: {score}/100 {emoji}

`
Include: Top 3 risks + links to research sources

### Export HTML
- Include inline CSS
- Add "Last Updated" timestamp
- Include research source links (clickable)
- Add "Refresh Data" button for dynamic update

---

## Key Dynamic Features

1. **Real-Time Risk Validation**: External news/search corroborates internal gut feel
2. **Adaptive Format**: Tables or prose based on content complexity
3. **YourCompany Context**: Risks scored against YourCompany-specific patterns (SSO, API, migration)
4. **Proactive Suggestions**: "Consider researching X based on Y signal"
5. **Trend Awareness**: "Similar deals with this risk profile had Z% win rate"

---

## Dependencies

- `GeminiService` — AI generation
- `WebSearchService` — Real-time risk research (NEW)
- `CRMService` — Historical deal patterns (NEW)
- `slackService.js` — Sharing
- `window.App.readFile(file)` — Attachments
- `localStorage` — Risk pattern learning

---

## YourCompany-Specific Risk Patterns

### Common Technical Risks:
- **SSO/SAML**: Complex configurations, multiple IdPs
- **Data Migration**: Legacy tool data export complexity
- **API Limits**: High-volume customers hitting rate limits
- **Custom Integrations**: Legacy system integration requirements
- **Compliance**: HIPAA, SOC2, GDPR requirements

### Common Business Risks:
- **Budget Freeze**: Economic downturn impact
- **Stakeholder Changes**: New CIO/CTO evaluation periods
- **Competitive Pressure**: Zendesk/Salesforce aggressive pricing
- **Timeline Compression**: End-of-quarter rush decisions
