---
name: exec-translator
description: Executive value translator with real-time executive research, dynamic persona adaptation, and C-level strategic messaging for YourCompany solutions
version: 2.0
author: YourCompany SE Team
last_updated: 2026-03-11
tags:
  - presales
  - executive
  - c-level
  - messaging
  - freshworks
  - solution-engineering
---
# SKILL: Exec Translator Module (Dynamic Edition)

**Module ID:** `execTranslator` | **File:** `src/modules/execTranslator.js`  
**Audience:** YourCompany Solution Engineering (Presales)  
**YourCompany Context:** Investor Day 2025, C-Suite Value Messaging

---

## Overview

AI-powered executive value translator with real-time executive research, dynamic persona adaptation, and context-aware messaging. Translates technical YourCompany features into C-level strategic value based on current executive priorities.

---

## Dynamic Executive Intelligence

### Real-Time Executive Research Protocol

For EACH target persona, AI MUST research:

1. **Executive Background & Priorities**:
   - Search LinkedIn `"{executive_name} {company} {title}"`
   - Search `"{executive_name} interview"` OR `"{executive_name} conference talk"`
   - Search `"{company} {executive_title} priorities 2024 2025"`
   - `[FETCH: Recent posts, articles, earnings call mentions]`

2. **Company Strategic Initiatives**:
   - Search `"{company} strategic priorities {current_year}"`
   - Search `"{company} earnings call transcript"` + `"{executive_title}"`
   - Search `"{company} investor day"` + `"{executive_title}"`
   - `[EXTRACT: Top 3 stated priorities relevant to this executive]`

3. **Industry & Role Context**:
   - Search `"{industry} {persona} challenges 2025"` (e.g., "healthcare CIO challenges")
   - Search `"{persona} priorities"` + `"{current_year}"` (e.g., "CFO priorities 2025")
   - `[MAP: YourCompany capabilities to these priorities]`

4. **Competitive Pressure**:
   - Search `"{company} vs competitors"` + `"customer experience"`
   - Search `"{industry} disruption"` OR `"{industry} digital transformation"`
   - `[IDENTIFY: Urgency drivers for this executive]`

---

## Inputs (Enhanced)

| Field ID | Label | Type | Dynamic Helper |
|----------|-------|------|----------------|
| `exec-feature` | Technical Feature | text | `[SUGGEST: From YourCompany product list]` |
| `exec-personas` | Target Persona | chip-group | CIO, CFO, CEO, COO, ALL |
| `exec-industry` | Industry Context | text | `[AUTO-FILL: From deal context]` |
| `exec-context` | Deal Context | textarea | `[LOAD: From MEDDPICC module]` |
| `exec-file` | Attachments | file (multi) | Technical specs, architecture |

---

## Persona Selection System (Enhanced)

### Dynamic Persona Adaptation:

Instead of static framing, use research-enriched personas:

**CIO (🖥️)**: 
- Static: IT governance, consolidation, risk
- **DYNAMIC**: `[FETCH: Recent CIO priorities from research]` + "Currently focused on {X} based on LinkedIn/interviews"

**CFO (💰)**:
- Static: Cost reduction, ROI, budget
- **DYNAMIC**: `[FETCH: Recent earnings/cost cutting initiatives]` + "Under pressure to reduce {X} spend"

**CEO (👔)**:
- Static: Competitive advantage, growth
- **DYNAMIC**: `[FETCH: Recent CEO statements]` + "Prioritizing {X} for {year}"

**COO (⚙️)**:
- Static: Efficiency, standardization
- **DYNAMIC**: `[FETCH: Operational initiatives]` + "Driving {X} transformation"

---

## Cross-Module Integration (Enhanced)

### loadFromDeal():

- Reads MEDDPICC fields
- **NEW**: Triggers executive research for identified stakeholders
- **NEW**: Suggests personas based on deal context

### setContext(context):

- Accepts enriched context with research data
- **NEW**: Auto-extracts executive names for targeted research

---

## AI Generation (Dynamic)

### Pre-Processing:

```
1. Identify target personas
2. For each persona: Perform external research (see protocol)
3. Map technical feature to persona's current priorities
4. Fetch YourCompany customer stories in same industry
5. Generate personalized value proposition
```

### Parallel Execution with Research:

- If ALL selected: Research all 4 personas simultaneously
- Generate cards sequentially but with research-enriched context
- Each card references specific research findings

### Dynamic Output Per Persona:

1. **Executive Summary** (Research-Personalized)
   - Strategic value proposition: `[Linked to specific priority from research]`
   - Key benefits: `[Mapped to stated initiatives]`
   - ROI impact: `[Framed in their vocabulary]`
   - Risk mitigation: `[Addressing their known concerns]`
   - Competitive advantage: `[Vs their known competitors]`
   - `[INCLUDE: "Based on {executive}'s focus on {priority}..."]`

2. **Strategic Benefits** (Priority-Aligned)

   | Benefit Category | Strategic Value | Business Impact | Evidence | KPI Impact | Complexity |

   **Dynamic:**
   - Categories match researched priorities
   - Evidence includes YourCompany customer stories in same industry
   - KPIs match executive's known metrics

3. **Detailed Benefit Framings** (Vocabulary-Matched)

   | Framing | Title | Explanation | Persona Focus | Supporting Metrics |

   **Adaptive:**
   - Uses executive's actual vocabulary from research
   - References their industry terminology
   - `[EXAMPLE: If CEO uses "customer obsession", use that framing]`

4. **Impact Summary** (Technical→Strategic→KPI)

   | Technical Aspect | Strategic Benefit | Persona KPI |

   **Mapped:**
   - Each technical feature → Their strategic goal → Their KPI
   - `[INCLUDE: "Addresses your {KPI} target of {X}" if known]`

5. **Financial Impact Analysis** (Context-Aware)

   | Cost Component | Current State | Proposed State | Savings/Value |

   **Enhanced:**
   - Uses company's actual financial context if researched
   - `[FETCH: Industry benchmarks for this role]`
   - `[SENSITIVITY: Ranges if exact numbers unknown]`

6. **Risk & Mitigation** (Concern-Specific)

   | Risk Category | Specific Risk | Probability | Impact | Mitigation |

   **Targeted:**
   - Addresses risks this specific executive typically worries about
   - `[EXAMPLE: CIO → Security, Integration; CFO → Budget overrun, ROI miss]`

7. **Recommended Talking Points** (Research-Informed)

   | Talking Point | Context | Persona Vocabulary | Expected Response | Follow-up |

   **Personalized:**
   - Opening hook references their recent talk/article/priority
   - Uses their preferred terminology
   - `[EXAMPLE: "I saw your post about {X}..."]`

8. **Persona-Specific Framing** (Priority-Aligned)
   - Priorities alignment: `[Mapped from research]`
   - Value proposition: `[In their words]`
   - `[INCLUDE: Direct quote from their interview if available]`

9. **Implementation Roadmap** (Role-Involved)

   | Phase | Activities | Timeline | Persona Involvement | Success Criteria |

   **Realistic:**
   - Timeline based on company's typical cycles (from research)
   - Persona involvement matches their actual role

10. **Success Metrics & KPIs** (Their Metrics)

    | KPI Category | Current State | Target State | Measurement |

    **Their Language:**
    - Uses KPIs they actually track (from research/role)
    - `[EXAMPLE: If CEO tracks NRR, use that; if CFO tracks Opex, use that]`

11. **Executive Summary for [Persona]** (Actionable)
    - Bottom line: `[One sentence summary]`
    - Strategic imperative: `[Why now, based on their context]`
    - Recommended action: `[Specific next step]`
    - Expected outcomes: `[By when]`
    - `[INCLUDE: "Given your focus on {X}, this enables..."]`

---

## Output Rendering (Enhanced)

### Per Card:

- Header: "{Persona} Value Translation | Research: {freshness}"
- Content: Research-referenced throughout
- AI badge + research source links
- `[BUTTON: "Refresh Executive Research"]`

### Copy Function:

- Includes research citations
- Suggests follow-up research actions

---

## Key Dynamic Features

1. **Executive Research**: Know what they care about before the call
2. **Vocabulary Matching**: Speak their language, not generic exec-speak
3. **Priority Alignment**: Connect to their stated initiatives
4. **Contextual Hooks**: Open with something relevant to them specifically
5. **KPI Matching**: Frame value in metrics they actually track

---

## Dependencies

- `GeminiService` — AI generation
- `WebSearchService` — Executive research (NEW)
- `LinkedInService` — Professional intel (NEW)
- `window.App.readFile(file)` — Attachments
- Cross-module: `DealMeddpicc` for stakeholder identification

---

## Persona Framing Guide

### CIO (Chief Information Officer):
- **Focus**: IT governance, system consolidation, risk, compliance, TCO, technical debt
- **YourCompany Value**: Unified platform reduces complexity, Freddy AI automates support
- **Key Message**: "Enterprise-grade without enterprise complexity"

### CFO (Chief Financial Officer):
- **Focus**: Cost reduction, headcount avoidance, predictable spend, ROI, NPV, cash flow
- **YourCompany Value**: 20% cost of complexity savings, headcount avoidance with Freddy AI
- **Key Message**: "Cost of Complexity" framework - eliminate waste

### CEO (Chief Executive Officer):
- **Focus**: Competitive advantage, revenue protection, customer experience, board metrics
- **YourCompany Value**: "Uncomplicated" customer experience, faster time-to-value
- **Key Message**: "Customer obsession" enabled by unified platform

### COO (Chief Operating Officer):
- **Focus**: Operational efficiency, process standardization, scalability, productivity
- **YourCompany Value**: Vertical AI agents, workflow automation, 80% deflection
- **Key Message**: "Operational excellence through AI-native platform"
