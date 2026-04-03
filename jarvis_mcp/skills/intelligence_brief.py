"""
IntelligenceBriefSkill — Nemotron 120B full-context synthesis pass.

Reads every account file with ZERO truncation, uses Nemotron's 1M token
context + maximum reasoning budget to synthesize a single Intelligence Brief
that becomes the primary context for all downstream skills.

Flow:
  discovery.md / deal_stage.json changes
    → IntelligenceBriefSkill (Nemotron, full context, reasoning_budget=16384)
    → intelligence_brief.md
    → cascades to meddpicc, battlecard, risk_report, value_arch, etc.
      (each reads the brief instead of raw fragmented files)
"""

import logging
from typing import Dict, Any
from jarvis_mcp.skills.base_skill import BaseSkill

log = logging.getLogger(__name__)


class IntelligenceBriefSkill(BaseSkill):
    """
    Nemotron full-context synthesis.  Runs first after any account update,
    then all reasoning skills cascade from its output.
    """

    MODEL_TYPE = "reasoning"   # → Nemotron 120B (1M ctx, reasoning_budget=16384)

    async def generate(self, account_name: str, **kwargs) -> str:
        context = await self.read_account_files(account_name)

        if not context:
            return "❌ No account data found — run discovery first."

        # ── Build FULL raw context — no truncation ────────────────────────────
        # Nemotron's 1M context handles everything.  We pass every file complete.
        raw_parts = []

        ds = context.get("deal_stage", "")
        if ds:
            raw_parts.append(f"=== DEAL DATA (structured) ===\n{ds}")

        disc = context.get("discovery", "")
        if disc:
            raw_parts.append(f"=== DISCOVERY NOTES (complete) ===\n{disc}")

        cr = context.get("company_research", "")
        if cr:
            raw_parts.append(f"=== COMPANY RESEARCH (complete) ===\n{cr}")

        # All other skill outputs — full, untruncated
        skip = {
            "deal_stage", "discovery", "company_research",
            "CLAUDE", "_deal", "_evolution_log", "_skill_timeline",
            "intelligence_brief",   # never include a stale brief in itself
        }
        for key, val in sorted(context.items()):
            if key not in skip and isinstance(val, str) and val.strip():
                raw_parts.append(
                    f"=== {key.upper().replace('_', ' ')} ===\n{val}"
                )

        evo = context.get("_evolution_log", "")
        if evo:
            raw_parts.append(f"=== EVOLUTION LOG ===\n{evo}")

        full_context = "\n\n".join(raw_parts)

        if not full_context.strip():
            return "❌ Account has no data yet — add discovery notes first."

        # ── Prompt — designed to maximise Nemotron's reasoning depth ─────────
        prompt = f"""You are performing a deep intelligence synthesis for sales account: {account_name}

COMPLETE ACCOUNT DATA — ALL FILES, ZERO TRUNCATION:
{full_context}

═══════════════════════════════════════════════════════════
YOUR TASK: MASTER INTELLIGENCE BRIEF
═══════════════════════════════════════════════════════════

You are the intelligence layer for a high-performing sales team.
Your brief will be the SOLE context given to downstream AI models
(MEDDPICC scoring, risk analysis, value architecture, battlecard,
proposal, competitive intel, meeting prep).

If a signal is in the data above, it MUST appear in your brief.
If something is missing or contradicted across files, flag it explicitly.
Reason across files — connect dots that a single-file reader would miss.

Write the following sections with maximum depth and accuracy:

## 1. Deal Overview
Stage, deal size, ARR, win probability, close date, product/solution,
key constraints, current momentum. Flag any inconsistencies in deal data.

## 2. Stakeholder Intelligence
Every person mentioned across ALL files:
- Full name, title, company role
- MEDDPICC role: Economic Buyer / Champion / Technical Buyer / Blocker / Influencer
- What they personally care about (their agenda, not the company's)
- Level of engagement: Active / Passive / Unknown
- Any risk signals (going cold, political blocker, budget authority unclear)
Champion(s): confirm who is actually advocating internally.
Economic Buyer: confirm who controls budget sign-off — NOT just who mentioned money.

## 3. Confirmed Pain Points & Business Impact
Every pain, problem, or frustration mentioned — with:
- The exact language the customer used (quote if available)
- Quantified business impact (cost, time, agents, percentage) if any was given
- Which MEDDPICC dimension it supports
Do NOT invent metrics. If a number was mentioned anywhere in any file, include it.

## 4. MEDDPICC Signal Map (complete cross-file analysis)
For EACH of the 8 dimensions, synthesize ALL evidence from ALL files:

**Metrics** — ROI numbers, cost savings, productivity gains, time savings
**Economic Buyer** — who controls budget, engagement level, risk of going dark
**Decision Criteria** — evaluation requirements, must-haves, scoring rubrics
**Decision Process** — approval chain, procurement steps, committee, timeline
**Paper Process** — legal, security, compliance review status, contract vehicle
**Implications** — confirmed pain with business consequence, urgency drivers
**Champion** — internal advocate strength, ability to influence, access to EB
**Competition** — every competitor mentioned, their status, how we compare

For each dimension: current status (GREEN/AMBER/RED), all supporting evidence, gaps.

## 5. Competitive Landscape
Every competitor mentioned across all files:
- Name, current status (active evaluation / eliminated / unknown / re-entering)
- Their known strengths in this account's context
- Our current positioning vs them
- Any pricing signals (their price, our price, gap)
- Risk level (threat / manageable / eliminated)

## 6. Technical Requirements & Integration Signals
Every technical requirement, integration, API, security, compliance, data residency,
performance, or migration signal mentioned anywhere. For each: confirmed / assumed / unknown.

## 7. Value & ROI Signals
Every budget signal, ROI claim, cost figure, efficiency metric, or quantified
business impact across all files. Group by: confirmed (customer stated) vs estimated.

## 8. Discovery Gaps — What We Don't Know
What is MISSING or UNCONFIRMED based on MEDDPICC:
- Which stakeholders have not been engaged
- Which decision criteria have not been confirmed
- Which technical requirements are assumed not confirmed
- What is blocking a GREEN score on each RED/AMBER MEDDPICC dimension
- Top 3 most important questions to ask in the next call

## 9. Deal Timeline & Momentum
All dates, deadlines, milestones, contract end dates, budget cycle dates.
Deal velocity: has the deal accelerated, stalled, or gone dark?
Key upcoming events and their impact on probability.

## 10. Cross-File Intelligence (signals only visible by reading everything)
List 3-7 insights that ONLY emerge from reading multiple files together —
contradictions, patterns, risks, or opportunities a single-file reader would miss.
Examples: "Discovery notes say CFO is engaged, but deal_stage shows probability
dropped — possible champion going cold." These cross-file insights are the most
valuable part of this brief.

═══════════════════════════════════════════════════════════
QUALITY RULES:
- Every claim must be traceable to the source data above
- Do NOT invent names, numbers, competitors, or timelines
- If something is TBD, say exactly what question would resolve it
- Include verbatim quotes from discovery notes where they add evidence
- This brief replaces ALL raw files for downstream skills — be complete
═══════════════════════════════════════════════════════════"""

        self.logger.info(
            f"IntelligenceBriefSkill: synthesising {len(raw_parts)} files "
            f"({len(full_context):,} chars) for {account_name}"
        )

        result = await self.llm.generate(
            prompt=prompt,
            model_type=self.MODEL_TYPE,
            system_prompt=self.grounded_system_prompt(),
            max_tokens=12000,   # Rich output — enough for a thorough brief
        )

        await self.write_output(account_name, "intelligence_brief.md", result)
        return result
