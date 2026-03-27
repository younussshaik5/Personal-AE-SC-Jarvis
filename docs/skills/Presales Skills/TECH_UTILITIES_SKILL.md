---
name: tech-utilities
description: Technical utilities suite with Email Assist, RFP Helper, and Objection Crusher - all with real-time research and current YourCompany product knowledge
version: 2.0
author: YourCompany SE Team
last_updated: 2026-03-11
tags:
  - presales
  - email
  - rfp
  - objections
  - technical
  - freshworks
  - solution-engineering
---
# SKILL: Technical Utilities Module (Dynamic Edition)

**Module ID:** `techUtilities` | **File:** `src/modules/techUtilities.js`  
**Audience:** YourCompany Solution Engineering (Presales)  
**YourCompany Context:** Technical Communications, RFPs, Objection Handling

---

## Overview

Container module hosting three AI-powered sub-modules with real-time research capabilities: Email Assist, RFP Helper, and Objection Crusher. All sub-modules fetch current information rather than relying on static knowledge.

---

## Container Logic (Enhanced)

### Tab Switching:

- Standard tab interface
- **NEW**: Persist sub-module state across tabs
- **NEW**: Share context between sub-modules (customer info, deal stage)

---

## Sub-Module 1: Email Assist (Dynamic)

**File:** `src/modules/tech/emailAssist.js`

### Purpose

Generate personalized, research-informed technical emails with current context.

### Inputs (Enhanced)

| Field ID | Label | Type | Dynamic Helper |
|----------|-------|------|----------------|
| `email-type` | Email Type | select | technical-reply, follow-up, poc-kickoff, exec-intro, proposal |
| `email-context` | Context / Thread | textarea | `[FETCH: Last email from CRM if available]` |
| `email-points` | Key Points to Cover | textarea | `[SUGGEST: Based on deal stage]` |
| `email-tone` | Tone | select | professional, friendly, executive, empathetic |
| `email-file` | Attachments | file (multi) | Reference docs |

### Dynamic Research Protocol

Before generating email:

1. **Recipient Research**:
   - Search recipient name/company for recent context
   - `[FETCH: Their recent LinkedIn activity, company news]`
   - `[IDENTIFY: Current priorities to reference]`

2. **Deal Context**:
   - `[FETCH: Stage, recent activities from CRM]`
   - `[IDENTIFY: Outstanding issues to address]`

3. **YourCompany Updates**:
   - `[FETCH: Recent product updates relevant to email topic]`
   - `[INCLUDE: New features released since last contact]`

### AI Generation (Research-Enhanced)

**System Persona:**
"YourCompany Solution Engineer writing personalized, timely technical emails"

**Required Sections:**

1. **Email Structure**
   - Subject lines: [3-5 options, incorporating current context]
   - Opening: [Personalized based on research]
   - Body: [Point integration with context]
   - Closing: [Next steps based on deal stage]

2. **Content Details**
   - Each section tied to specific research finding
   - `[INCLUDE: Reference to their recent news/priority]`

3. **Key Points Integration**
   - Mapped to their stated priorities
   - `[PRIORITIZE: Based on deal stage and urgency]`

4. **Tone & Style**
   - Matched to recipient's communication style (from research)
   - Industry-appropriate terminology

5. **Follow-up Strategy**
   - Timeline based on their typical response patterns
   - `[SUGGEST: Optimal send time based on role]`

6. **Alternative Versions**
   - Shorter version for mobile
   - Executive summary version
   - Technical detail version

**Output:**

- Full email with `[PERSONALIZATION NOTES]` showing research usage
- Copy button with research citations

---

## Sub-Module 2: RFP Helper (Dynamic)

**File:** `src/modules/tech/rfpHelper.js`

### Purpose

Process RFPs with real-time technical research and current product capabilities.

### State Object (Enhanced)

```js
{
  data: [],
  headers: [],
  questionCol: null,
  processing: false,
  sheets: [],
  finalSpec: '',
  architecture: '',
  totalRows: 0,
  processedRows: 0,
  errorCount: 0,
  startTime: null,
  endTime: null,
  currentSheet: null,
  currentRow: null,
  isPaused: false,
  retryQueue: [],
  // NEW: Research cache
  researchCache: {}, // {question_hash: research_results}
  productVersion: null // YourCompany version for accuracy
}
```

### 3-Step UI Flow (Enhanced)

**Step 1 — Upload:**

- Parse Excel/CSV
- **NEW**: Detect RFP type (Technical, Security, Functional)
- **NEW**: Suggest processing mode based on detected type

**Step 2 — Configure:**

- Sheet selector
- Mode: "Answer Questions" OR "Rephrase / Generate Questions"
- Column selector
- **NEW**: "Research Current Product Capabilities" toggle

**Step 3 — Processing & Review:**

- Live progress
- **NEW**: Per-question research indicator
- Editable table with research sources
- **NEW**: "Re-research" button for stale answers

### Concurrency Model (Research-Enhanced)

**Per-Row Processing with Research:**

```js
async processSingleRow(i) {
  const question = this.data[i][this.questionCol];

  // 1. Check research cache
  if (!this.researchCache[hash(question)]) {
    // 2. Research current capabilities
    this.researchCache[hash(question)] = await this.researchCapability(question);
  }

  // 3. Generate answer with research context
  const answer = await this.generateAnswer(question, researchContext);

  // 4. Validate against current product version
  if (this.productVersion) {
    answer = this.validateVersion(answer, this.productVersion);
  }

  return answer;
}
```

**Research Capability Method:**

- Search YourCompany docs for feature
- Search `"YourCompany {feature} {current_year}"`
- Check release notes for recency
- `[RETURN: Current capability + source + version]`

**Fallback Chain:**

1. Primary model with research context
2. If "NOT FOUND": Search broader web for YourCompany capability
3. If still not found: "Contact Product Team for Roadmap Status"

### Final Architecture Generation (Current)

**Input:** All Q&A with research sources
**Model:** Current YourCompany architecture expert
**Output:**

- Comprehensive architecture using current product names
- **INCLUDE: Version-aware caveats ("As of v{X}...")**
- **FLAG: Features in beta/preview**

### Export (Enhanced)

- Excel with "Sources" column (URLs to research)
- "Product Version" sheet with version used
- "Changelog" sheet noting answers that may need refresh

---

## Sub-Module 3: Objection Crusher (Dynamic)

**File:** `src/modules/tech/objectionCrusher.js`

### Purpose

Handle objections with real-time competitive intelligence and current proof points.

### Inputs (Enhanced)

| Field ID | Label | Type | Dynamic Helper |
|----------|-------|------|----------------|
| `objection-input` | The Objection | textarea | `[SUGGEST: Common objections from deal context]` |
| `objection-type` | Objection Type | select | company-size, pricing, features, security, competition |
| `objection-file` | Attachments | file (multi) | Competitor claims, comparison docs |

### Dynamic Research Protocol

Before generating response:

1. **Objection Analysis**:
   - Parse objection for specific claims
   - `[IDENTIFY: Competitor mentioned, specific features/pricing cited]`

2. **Competitive Research**:
   - If competitor mentioned: Search `"{competitor} {claim}"`
   - `[VERIFY: Is the claim accurate?]`
   - `[FETCH: YourCompany counter-evidence]`

3. **Proof Point Research**:
   - Search `"YourCompany {objection_type} case study"`
   - `[FETCH: Recent customer wins, ROI data]`
   - `[FETCH: G2 comparisons for this specific objection]`

4. **Current Positioning**:
   - `[FETCH: Latest YourCompany messaging on this topic]`
   - `[INCLUDE: Investor Day 2025 themes if relevant]`

### EPC Framework (Research-Enhanced)

**Empathy Phase:**

- Acknowledge specific concern
- `[VALIDATE: Is this concern valid based on research?]`
- Show understanding of their context

**Proof Phase:**

- Evidence from research (not generic)
- `[INCLUDE: Specific customer example in their industry]`
- `[INCLUDE: Current G2/data from research]`
- `[SOURCE: All evidence cited]`

**Challenger Phase:**

- Reframe based on their specific situation
- `[USE: Research about their company/priorities]`
- Expose the real question they should be asking

### AI Generation (Current)

**Required Sections:**

1. **Executive Summary**
   - Objection analysis with research context
   - Root cause: `[Based on deal research]`
   - Strategy: `[Attack/Defend/Reframe based on evidence]`

2. **Empathy Phase** (Context-Aware)
   - Validation of their specific concern
   - `[REFERENCE: Their industry/company situation]`

3. **Proof Phase** (Evidence-Based)
   - Current data from research
   - `[TABLE: Claim vs Fact vs Source]`
   - Customer stories: [Recent, relevant, sourced]

4. **Challenger Phase** (Situation-Specific)
   - Reframe using their priorities (from research)
   - Question to ask: `[Specific to their context]`

5. **Objection-Specific Strategy**
   - Tactic based on deal stage and research
   - Key messages: `[Using current YourCompany positioning]`

6. **Competitive Intelligence** (Live)
   - Competitor claim: `[As stated in objection]`
   - YourCompany counter: `[With current evidence]`
   - `[TABLE: Side-by-side with sources]`

7. **Follow-up Actions**
   - Specific next steps based on objection type
   - `[SUGGEST: Resources to send, people to involve]`

---

## Shared Dependencies (All Sub-Modules)

- `GeminiService` — AI generation
- `WebSearchService` — Real-time research (NEW)
- `YourCompanyDocsService` — Current product docs (NEW)
- `G2Service` — Review data (NEW)
- `ExcelHandler` — File processing
- `XLSX` — Export

---

## Key Dynamic Features

1. **Current Product Knowledge**: Not relying on training data cutoff
2. **Competitive Verification**: Fact-check competitor claims in real-time
3. **Personalized Communication**: Research-informed, not template-based
4. **Version Awareness**: "As of v{X}" for accuracy
5. **Source Citations**: Every claim has a source

---

## YourCompany Objection Handling Reference

### Common Objections:

**"We're already using Zendesk/Salesforce"**
- Empathy: "They've been the standard for years"
- Proof: "But customers report 20% waste on complexity"
- Challenger: "What if you could achieve same outcomes with half the admin overhead?"

**"Your AI isn't as good as competitors"**
- Empathy: "AI claims are everywhere now"
- Proof: "Freddy AI resolves 80% of routine queries - higher than industry average"
- Challenger: "Are you measuring resolution rate or just feature count?"

**"We need enterprise-grade security"**
- Empathy: "Security is non-negotiable"
- Proof: "SOC 2 Type II, HIPAA, GDPR compliant - same certifications as competitors"
- Challenger: "What specific requirements do you have that we haven't met?"

**"The price is too high"**
- Empathy: "Budget pressure is real"
- Proof: "TCO analysis shows 30% savings over 3 years vs Zendesk Enterprise"
- Challenger: "Are you comparing license costs or total cost of ownership?"
