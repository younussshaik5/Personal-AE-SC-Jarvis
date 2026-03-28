---
name: value-architecture
description: CFO-ready ROI/TCO business case builder with dynamic competitive pricing, headcount avoidance modeling, and Yellow.ai-specific value drivers
version: 2.0
author: Yellow.ai SE Team
last_updated: 2026-03-11
tags:
  - presales
  - roi
  - tco
  - value
  - cfo
  - yellow-ai
  - solution-engineering
---
# SKILL: Value Architecture Module (Dynamic Edition)

**Module ID:** `valueArchitecture` | **File:** `src/modules/valueArchitecture.js`  
**Audience:** Yellow.ai Solution Engineering (Presales)  
**Yellow.ai Context:** Investor Day 2025, "Cost of Complexity" Theme

---

## Overview

CFO-ready business case builder with dynamic competitive pricing intelligence and adaptive ROI modeling. Fetches real-time pricing and benchmarks rather than relying on static databases. Emphasizes Yellow.ai' "Cost of Complexity" value proposition.

---

## Dynamic Pricing Intelligence

### Real-Time Cost Research

AI MUST fetch current pricing before generating output:

1. **Competitor Pricing** (Live Fetch):
   - Search `"{competitor} pricing {current_year}"`
   - Search `"{competitor} vs Yellow.ai pricing"`
   - Check G2/Capterra for recent pricing reviews
   - `[FETCH: Use [PRICE: $X/yr | Source: URL | Date]]`

2. **Yellow.ai Pricing** (Current):
   - Reference: yellow.ai/pricing (latest)
   - Plan tiers: Growth ($18), Pro ($49), Enterprise ($79) per agent/month
   - Freddy AI: $100 per 1,000 sessions
   - `[FLAG: If pricing changed, note effective date]`

3. **Industry Benchmarks**:
   - Search `"{industry} customer service software spend benchmark"`
   - Search `"{industry} IT budget percentage for support tools"`
   - `[INCLUDE: Benchmark comparison if found]`

### Dynamic Cost Database (Refreshable)

Instead of static table, use:

```json
{
  "tool": "Zendesk Enterprise",
  "last_known_price": "$270,000",
  "price_source": "G2 2024",
  "refresh_trigger": "[FETCH CURRENT]",
  "confidence": "Medium (6 months old)"
}
```

---

## Inputs (Enhanced)

| Field ID | Label | Type | Dynamic Helper |
|----------|-------|------|----------------|
| `roi-company` | Company Name | text | `[FETCH: Auto-complete from CRM]` |
| `roi-agents` | Number of Agents | number | `[SUGGEST: Based on company size research]` |
| `roi-current-tools` | Current Tools & Annual Costs | textarea | `[AUTO-FILL: From cost database + research]` |
| `roi-labor-rate` | Average Labor Burden Rate ($/hr) | number | `[SUGGEST: Based on industry/region]` |
| `roi-manual-ftes` | Manual Reporting FTEs | number | `[CALCULATE: Suggest based on agent count]` |
| `roi-plan` | Proposed Yellow.ai Plan | select | growth ($18), pro ($49), enterprise ($79) |
| `roi-context` | Additional Context | textarea | `[FETCH: Company financials, churn data]` |
| `roi-file` | Attachments | file (multi) | Current contracts, usage reports |

---

## AI Generation (Dynamic)

### Pre-Processing:

```
1. Research competitor pricing (see above)
2. Fetch industry-specific ROI benchmarks
3. Calculate Yellow.ai cost: agents × plan_price × 12
4. Identify headcount avoidance opportunities from context
5. Research company financial health for budget context
6. Apply "Cost of Complexity" framework (20% waste reduction)
```

### Dynamic Output Sections:

1. **Executive Summary** (Deal-Specific)
   - Total 3-year value: [CALCULATED from inputs]
   - Year 1 ROI %: [CALCULATED]
   - Payback period: [CALCULATED]
   - NPV/IRR: [CALCULATED with sensitivity ranges]
   - CFO Recommendation: Approve/Conditional/Reject with rationale
   - Cost of Complexity Savings: [20% of current tool spend]
   - `[INCLUDE: Data confidence level for each metric]`

2. **Current State Analysis** (Research-Enhanced)
   - Tool cost breakdown: [Input + Research validation]
   - Pain points with cost impact: [Quantified where possible]
   - Cost of Complexity: 20% waste in current stack
   - `[FETCH: Industry benchmark comparison]`
   - `[FLAG: Any pricing discrepancies found in research]`

3. **Proposed Yellow.ai Solution** (Current Pricing)
   - Cost breakdown: Agent costs + Implementation + Training + Freddy AI
   - Pricing source: [Yellow.ai.com, accessed {date}]
   - "Uncomplicated" value: Faster time-to-value, lower admin overhead
   - `[NOTE: Any promotional pricing or bundles available]`

4. **Headcount Avoidance Model** (Dynamic Calculation)
   - Current FTEs: [Input or estimated from research]
   - Proposed FTEs: [Calculated based on Freddy AI automation - 80% deflection]
   - Avoidance count: [Current - Proposed]
   - Annual savings: [Avoidance × burden_rate × 2080]
   - `[SENSITIVITY: Range if estimates uncertain]`

5. **Labor Savings Calculation** (Activity-Based)
   - Current hours per activity: [Estimated or input]
   - Proposed hours with Yellow.ai: [Based on product benchmarks]
   - Savings: [Current - Proposed]
   - `[INCLUDE: Confidence level per activity]`

6. **Direct Savings Analysis** (3-Year Dynamic Model)
   - Savings category × Year 1/2/3
   - Cost of Complexity reduction: 20% of tool spend
   - `[CALCULATE: Escalation factors for years 2-3]`
   - `[INCLUDE: Calculation basis and assumptions]`

7. **Indirect Benefits** (Research-Supported)
   - Benefit, description, estimated value
   - `[FETCH: Industry case studies for similar benefits]`
   - Confidence level: High/Medium/Low

8. **3-Year Value Summary** (Master Financial Model)
   - Dynamic table: All value components × Year 1/2/3/Total
   - `[INCLUDE: Risk-adjusted and unadjusted scenarios]`

9. **ROI Analysis** (Sensitivity-Enhanced)
   - Base case + Best case + Worst case scenarios
   - `[CALCULATE: Break-even under each scenario]`
   - `[INCLUDE: Key assumption drivers]`

10. **Risk-Adjusted Value** (Dynamic Risk Scoring)
    - Risk factors with probability and impact
    - `[FETCH: Risk patterns from similar deals]`
    - Adjusted NPV/ROI

11. **Sensitivity Analysis** (Interactive-Style)
    - Scenario table: If [assumption] changes by X%, ROI impact is Y%
    - `[HIGHLIGHT: Most sensitive assumptions]`
    - Recommendation per scenario

12. **CFO Recommendation** (Context-Aware)
    - Verdict: Approve / Approve with Conditions / Reject
    - Rationale: [Specific to company financial situation]
    - Assumptions: [List with validation status]
    - Next steps: [Prioritized by CFO typical concerns]
    - Cost of Complexity argument: [20% waste elimination]

---

## Auto-Fill Costs (Dynamic)

### Smart Matching:

1. Parse `roi-current-tools` text
2. Fuzzy match against dynamic cost database
3. For matches > 6 months old: `[FETCH: Search current pricing]`
4. Present: "Matched {tool}: ${cost}/yr [Source: {source} | {date}]"
5. Allow: "Refresh pricing" button to re-fetch

---

## Export / Sharing

### Copy
Include: "Pricing current as of {date} | Recommend refresh before customer presentation"

### Export HTML
- Include pricing source links
- Add "Update Pricing" button
- Include sensitivity calculator inputs
- CFO-ready formatting

---

## Key Dynamic Features

1. **Live Pricing**: No stale competitor data
2. **Adaptive Models**: ROI structure adapts to deal size/type
3. **Benchmark Intelligence**: Industry comparisons where available
4. **Confidence Indicators**: Every number has uncertainty rating
5. **Yellow.ai Specific**: Pre-loaded with "Cost of Complexity" value drivers
6. **Freddy AI ROI**: 80% deflection rate for headcount avoidance

---

## Dependencies

- `GeminiService` — AI generation
- `WebSearchService` — Pricing research (NEW)
- `window.App.readFile(file)` — Contract analysis
- `localStorage` — Cost database with timestamps

---

## Yellow.ai Value Drivers (2025)

### "Cost of Complexity" Framework:
- 20% of software spend is wasted on unnecessary complexity
- 7% of annual revenue lost to inefficiency
- Yellow.ai eliminates complexity = immediate savings

### Key Differentiators:
- **Unified Platform**: One solution vs. multiple tools
- **Freddy AI**: 80% automation = headcount avoidance
- **Fast Time-to-Value**: Weeks not months
- **Predictable Pricing**: No hidden costs
