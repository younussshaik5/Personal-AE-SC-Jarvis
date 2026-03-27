#!/usr/bin/env python3
"""Data aggregation utilities for cross-skill synchronization."""

import json
from pathlib import Path
from typing import Dict, Any


def read_all_skill_data(account_folder: Path) -> Dict[str, Any]:
    """Read all skill-generated document files into a unified context.
    
    Does NOT include core data (deals, notes, summary) — those are read separately by each skill.
    """
    context = {
        'discovery': {},
        'risk_assessment': '',
        'meddpicc': {},
        'tech_utilities': {},
        'battlecards': {},
        'value_architecture': {},
        'risk_report': '',
        'demo_strategy': {}
    }

    # Discovery folder
    discovery_dir = account_folder / 'discovery'
    if discovery_dir.exists():
        for doc in ['internal_discovery.md', 'final_discovery.md', 'Q2A.md']:
            fpath = discovery_dir / doc
            if fpath.exists():
                context['discovery'][doc.replace('.md', '')] = fpath.read_text(encoding='utf-8')[:2000]

    # Technical Risk Assessment (root file)
    risk_file = account_folder / 'TECHNICAL_RISK_ASSESSMENT.md'
    if risk_file.exists():
        context['risk_assessment'] = risk_file.read_text(encoding='utf-8')[:2000]

    # MEDDPICC folder
    meddpicc_dir = account_folder / 'meddpicc'
    if meddpicc_dir.exists():
        for doc in ['qualification_report.md', 'stakeholder_analysis.md']:
            fpath = meddpicc_dir / doc
            if fpath.exists():
                context['meddpicc'][doc.replace('.md', '')] = fpath.read_text(encoding='utf-8')[:2000]

    # Tech Utilities folder
    utils_dir = account_folder / 'tech_utilities'
    if utils_dir.exists():
        for doc in ['email_templates.md', 'email_generation.md', 'objection_handling.md', 'rfp_helper.md']:
            fpath = utils_dir / doc
            if fpath.exists():
                context['tech_utilities'][doc.replace('.md', '')] = fpath.read_text(encoding='utf-8')[:2000]

    # Battlecards folder
    bc_dir = account_folder / 'battlecards'
    if bc_dir.exists():
        for doc in ['competitive_intel.md', 'pricing_comparison.md', 'discovery_questions.md']:
            fpath = bc_dir / doc
            if fpath.exists():
                context['battlecards'][doc.replace('.md', '')] = fpath.read_text(encoding='utf-8')[:2000]

    # Value Architecture folder
    va_dir = account_folder / 'value_architecture'
    if va_dir.exists():
        for doc in ['roi_model.md', 'tco_analysis.md']:
            fpath = va_dir / doc
            if fpath.exists():
                context['value_architecture'][doc.replace('.md', '')] = fpath.read_text(encoding='utf-8')[:2000]

    # Risk Reports folder
    risk_report_dir = account_folder / 'risk_reports'
    if risk_report_dir.exists():
        for doc in ['deal_risk_assessment.md']:
            fpath = risk_report_dir / doc
            if fpath.exists():
                context['risk_report'] = fpath.read_text(encoding='utf-8')[:2000]

    # Demo Strategy folder
    demo_dir = account_folder / 'demo_strategy'
    if demo_dir.exists():
        for doc in ['demo_strategy.md', 'tech_talking_points.md', 'demo_script.md']:
            fpath = demo_dir / doc
            if fpath.exists():
                context['demo_strategy'][doc.replace('.md', '')] = fpath.read_text(encoding='utf-8')[:2000]

    return context
