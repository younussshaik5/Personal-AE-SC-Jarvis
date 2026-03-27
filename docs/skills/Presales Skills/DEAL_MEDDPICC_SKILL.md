---
name: deal-meddpicc
description: Comprehensive MEDDPICC qualification with real-time stakeholder research, dynamic scoring, and deal-specific risk assessment for enterprise deals
version: 2.0
author: YourCompany SE Team
last_updated: 2026-03-11
tags:
  - presales
  - meddpicc
  - qualification
  - enterprise
  - freshworks
  - solution-engineering
---
# SKILL: Deal MEDDPICC Module (Dynamic Edition)

**Module ID:** `dealMeddpicc` | **File:** `src/modules/dealMeddpicc.js`  
**Audience:** YourCompany Solution Engineering (Presales)  
**YourCompany Context:** Enterprise Deal Qualification, Field Sales Motion

---

## Overview

AI-powered MEDDPICC qualification with real-time stakeholder research, dynamic scoring, and deal-specific risk assessment. Optimized for YourCompany enterprise deals with mid-market and enterprise customers (250+ employees).

---

## Dynamic Deal Intelligence

### Real-Time Research Protocol

Before generating analysis, AI MUST research:

1. **Company Intelligence**:
   - Search `"{company} earnings Q{current_quarter} {current_year}"`
   - Search `"{company} IT spending"` OR `"{company} digital transformation"`
   - Search `"{company} layoffs"` OR `"{company} hiring freeze"` (risk signals)
   - `[FETCH: 10-K/Annual report for public companies]`

2. **Stakeholder Research**:
   - Search LinkedIn `"{company} CIO CTO VP Customer Service"`
   - Search `"{company} leadership changes 2024 2025"`
   - `[FETCH: Decision maker backgrounds, tenure, priorities]`

3. **Competitive Context**:
   - Search `"{company} {current_tool} contract renewal"`
   - Search `"{company} customer service platform RFP"`
   - `[IDENTIFY: Competitive threats and timing]`

4. **Industry Dynamics**:
   - Search `"{industry} customer experience trends 2025"`
   - Search `"{industry} regulatory changes"`
   - `[MAP: Industry-specific pain points to MEDDPICC]`

---

## Inputs (Enhanced)

| Field ID | Label | Type | Dynamic Helper |
|----------|-------|------|----------------|
| `meddpicc-deal` | Deal Name | text | `[FETCH: Auto-complete from CRM]` |
| `meddpicc-value` | Deal Value (ARR) | text | `[CALCULATE: From agent count × plan × 12]` |
| `meddpicc-notes` | Discovery Notes | textarea (10 rows) | `[AUTO-ENRICH: From CRM + research]` |
| `meddpicc-file` | Attachments | file (multi) | Account plans, org charts |

---

## CRM Integration (Enhanced)

### Fetch from CRM:

1. Check `YourCompanyService.isConnected()`
2. Get deals with enrichment:
   - Deal fields: name, amount, stage, probability, expected_close
   - **NEW**: Auto-research fetched deals for external context
   - **NEW**: Flag deals with recent stakeholder changes
3. Render deal list with risk indicators:
   - 🟢 Low risk: Good MEDDPICC coverage
   - 🟡 Medium: Gaps identified
   - 🔴 High: Critical gaps + external risk signals

### Select Deal:

- Populate fields
- **NEW**: Trigger background research
- Show toast: "Selected: {deal.name} | Researching external context..."

---

## AI Analysis (Dynamic)

### Pre-Processing:

```
1. Parse discovery notes for MEDDPICC signals
2. Perform external research (see protocol)
3. Cross-reference with similar closed deals (win/loss patterns)
4. Identify deal-specific MEDDPICC weights (e.g., Compliance-heavy for Healthcare)
5. Generate scored assessment with confidence levels
```

### Dynamic Output Sections:

1. **Executive Summary** (Deal-Health Score)
   - Deal Health Score: X/100 [Weighted by deal size + industry]
   - Risk Level: 🔴/🟡/🟢 with specific rationale
   - Win Probability: % [Based on similar deals + current MEDDPICC]
   - Critical Success Factors: [5-7 deal-specific factors]
   - Top 3 Priority Actions: [Ranked by impact + urgency]
   - Timeline Risk: [Based on fiscal calendar research]
   - Resource Requirements: [SE + management + partner]

2. **MEDDPICC Scorecard** (Weighted Scoring)

   | Dimension | Score /10 | Weight | Weighted Score | Indicator | Key Finding | Evidence | Gap Analysis | Recommended Action |

   **Dynamic Weighting by Deal Type:**
   - Enterprise: Economic Buyer (1.2x), Paper Process (1.2x)
   - Mid-Market: Metrics (1.1x), Champion (1.1x)
   - Compliance-heavy: Decision Criteria (1.2x)
   - Competitive deal: Identify Pain (1.2x)

   Scoring Legend: 🟢 7-10 | 🟡 4-6 | 🔴 1-3
   Dimensions: **M**etrics, **E**conomic Buyer, **D**ecision Criteria, **D**ecision Process, **I**dentify Pain, **P**aper Process, **I**mplicate Pain, **C**hampion

3. **Detailed Assessment by Dimension** (Research-Enhanced)

   Each dimension includes:
   - Dimension-specific fields (e.g., M: Current Metrics from research)
   - Gap Analysis: [Internal notes + external context]
   - Recommended Actions: [3-5 prioritized steps]
   - `[FETCH: Industry benchmarks for this dimension]`

4. **Stakeholder Analysis** (Dynamic Research)

   | Stakeholder | Role | Influence | Engagement | Risk Level | Mitigation Strategy |

   **Enhanced with Research:**
   - Auto-identified stakeholders from LinkedIn/web
   - Background/priorities from public sources
   - Connection paths (mutual connections, past vendors)
   - `[FLAG: New hires or recent departures as risk]`

5. **Competitive Landscape** (Live Intel)

   | Competitor | Strengths | Weaknesses | Our Advantage | Strategy |

   **Dynamic:**
   - Identified from notes + research
   - Recent competitive moves (pricing, features)
   - Win/loss history from CRM
   - `[FETCH: G2 sentiment for each competitor]`

6. **Risk Assessment** (Multi-Source)

   | Risk Category | Specific Risk | Probability | Impact | Mitigation | Contingency |

   **Sources:**
   - Internal: From discovery notes
   - External: From web research (budget, leadership changes)
   - Historical: From similar deal patterns
   - `[SORTED BY: Risk score = Probability × Impact]`

7. **Timeline & Milestones** (Fiscal-Aware)

   | Milestone | Date | Owner | Status | Dependencies | Risk |

   **Enhanced:**
   - Aligned to customer's fiscal calendar (from research)
   - Critical path highlighting
   - `[FLAG: Milestones at risk based on current progress]`

8. **Deal Health Summary** (Actionable)
   - Score/100 with trend (↑/↓/→)
   - Risk level with specific threats
   - Win probability with confidence interval
   - Top 10 Priority Actions: [Numbered, with owners]
   - Timeline impact: [Days to close vs. typical cycle]
   - Resource impact: [SE hours + management hours needed]

9. **Next Steps** (Prioritized)

   | Action | Owner | Due Date | Status | Dependencies |

   **Smart Prioritization:**
   - MEDDPICC gaps ranked by deal impact
   - Auto-suggested owners based on role
   - `[REMINDER: Links to calendar for scheduling]`

---

## Cross-Module Integration

### Exec Translator Integration:

- `loadFromDeal()` reads MEDDPICC fields
- **NEW**: Also passes research-enriched context
- Enables: MEDDPICC analysis → Exec messaging in one flow

### Risk Report Integration:

- **NEW**: Auto-generate Risk Report from MEDDPICC gaps
- Share risk data between modules

---

## Key Dynamic Features

1. **External Data Integration**: Not just what's in CRM, but what's happening in the market
2. **Adaptive Scoring**: Different MEDDPICC weights for different deal types
3. **Stakeholder Intelligence**: Auto-research decision makers
4. **Risk Correlation**: Connects internal gaps to external threats
5. **Fiscal Awareness**: Timeline recommendations based on customer's fiscal calendar

---

## Dependencies

- `GeminiService` — AI generation
- `YourCompanyService` — CRM integration
- `WebSearchService` — Company/stakeholder research (NEW)
- `LinkedInService` — Professional network intel (NEW)
- `slackService.js` — Sharing

---

## MEDDPICC Quick Reference

### The 8 Dimensions:
- **M**etrics: Quantifiable business outcomes
- **E**conomic Buyer: Final decision maker with budget authority
- **D**ecision Criteria: How they'll evaluate solutions
- **D**ecision Process: Steps to purchase approval
- **P**aper Process: Legal, security, procurement requirements
- **I**dentify Pain: Business challenges driving the deal
- **I**mplicate Pain: Consequences of inaction
- **C**hampion: Internal advocate who sells for you
- **C**ompetition: Direct competitors, alternatives, status quo

### Scoring Guide:
- 🟢 Green (7-10): Confirmed and tested
- 🟡 Yellow (4-6): Partial or unverified
- 🔴 Red (1-3): No information

### YourCompany Context:
- **Mid-Market**: 250-5,000 employees
- **Enterprise**: 5,000+ employees
- **Target**: 60%+ of ARR from mid-market & enterprise
