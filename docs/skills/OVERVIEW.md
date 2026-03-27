# JARVIS Skills Overview

JARVIS is built on a modular "Skill" architecture. Each skill is a specialized Python class responsible for a specific aspect of sales engineering documentation or account intelligence.

## Core Documentation Skills

### 1. Technical Risk Assessment (`technical_risk_assessment.py`)
- **Function**: Analyzes account data to identify technical risks and knowledge gaps.
- **Output**: `TECHNICAL_RISK_ASSESSMENT.md`
- **Logic**: Uses LLM to synthesize risks from notes, deals, and conversations.

### 2. Discovery Management (`discovery_management.py`)
- **Function**: Manages the end-to-end discovery process.
- **Output**: `discovery/internal_discovery.md`, `discovery/final_discovery.md`, `discovery/Q2A.md`
- **Logic**: Maps current state vs. desired state; tracks open questions.

### 3. Account Dashboard (`account_dashboard_skill.py`)
- **Function**: The "Master View" of an account.
- **Output**: `DASHBOARD.html`
- **Logic**: Aggregates data from ALL other skills; provides KPI bars and interactive tables.

## Strategy & Qualification Skills

### 4. Deal MEDDPICC (`deal_meddpicc.py`)
- **Function**: Tracks deal qualification using the MEDDPICC framework.
- **Output**: `meddpicc/qualification_report.md`
- **Logic**: Identified Champion, Economic Buyer, Decision Criteria, etc.

### 5. Stakeholder Analysis (`stakeholder_analysis.py`)
- **Function**: Maps out the political and technical landscape of an account.
- **Output**: `meddpicc/stakeholder_analysis.md`
- **Data**: Pulls from LinkedIn research and OpenCode conversations.

### 6. Demo Strategy (`demo_strategy.py`)
- **Function**: Recommends a tailored demo flow based on discovery.
- **Output**: `demo_strategy/demo_strategy.md`
- **Logic**: Matches prospect pain points to specific product features.

## Value Architecture Skills

### 7. ROI Model (`roi_model.py`)
- **Function**: Calculates the potential financial impact of the solution.
- **Output**: `value_architecture/roi_model.md`
- **Logic**: Uses industry benchmarks and prospect-provided data points.

### 8. TCO Analysis (`tco_analysis.py`)
- **Function**: Compares Total Cost of Ownership against competitors.
- **Output**: `value_architecture/tco_analysis.md`
- **Logic**: Includes implementation, support, and hidden costs.

## Intelligence & Research Skills

### 9. Battlecards (`battlecards.py`)
- **Function**: Provides competitive intelligence.
- **Output**: `battlecards/competitive_intel.md`
- **Logic**: Real-time extraction of competitor mentions in conversations.

### 10. Pricing Comparison (`pricing_comparison.py`)
- **Function**: Compares product pricing vs. market alternatives.
- **Output**: `battlecards/pricing_comparison.md`

## Utility & Management Skills

### 11. Documentation Skill (`documentation.py`)
- **Function**: Manages the library of generated materials and user requests.

### 12. Account Initialization (`account_initialization.py`)
- **Function**: Automatically sets up the folder structure for new accounts.

---

## How Skills Work Together

Skills are **interlinked** via the `EventBus` and the `DataAggregator`.
- When `DiscoveryManagementSkill` updates a pain point, the `RiskAssessmentSkill` is triggered to re-evaluate the risk level.
- The `AccountDashboardSkill` runs last, pulling data from all generated files to provide the final unified view.
