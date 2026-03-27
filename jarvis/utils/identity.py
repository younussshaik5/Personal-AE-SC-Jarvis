#!/usr/bin/env python3
"""JARVIS Identity Module - Provides consistent SE identity across all components."""

from dataclasses import dataclass
from typing import Optional
from jarvis.utils.config import ConfigManager


@dataclass
class SEIdentity:
    """Solution Engineer identity information."""
    name: str
    initials: str
    title: str
    full_display: str
    signature: str


def get_se_identity(config_manager: Optional[ConfigManager] = None) -> SEIdentity:
    """Get the configured SE identity.
    
    Args:
        config_manager: Optional ConfigManager instance. If None, creates one.
    
    Returns:
        SEIdentity object with name, initials, title, etc.
    """
    if config_manager is None:
        config_manager = ConfigManager()
        config_manager.load()
    
    se_config = getattr(config_manager.config, 'solution_engineer', None)
    if se_config:
        name = getattr(se_config, 'name', 'YOUR_NAME')
        initials = getattr(se_config, 'initials', 'SE')
        title = getattr(se_config, 'title', 'Solution Engineer')
    else:
        # Fallback defaults
        name = 'YOUR_NAME'
        initials = 'SE'
        title = 'Solution Engineer'
    
    full_display = f"{initials} {name}"
    signature = f"{initials} {name}"
    
    return SEIdentity(
        name=name,
        initials=initials,
        title=title,
        full_display=full_display,
        signature=signature
    )


def format_se_signature(date: Optional[str] = None, include_title: bool = True) -> str:
    """Get a formatted SE signature for file headers.
    
    Args:
        date: Optional date string. If None, uses current date.
        include_title: Whether to include the title.
    
    Returns:
        Formatted signature string.
    """
    from datetime import datetime
    identity = get_se_identity()
    date_str = date or datetime.now().strftime("%Y-%m-%d")
    
    if include_title:
        return f"{identity.initials} {identity.name} | {identity.title} | {date_str}"
    return f"{identity.initials} {identity.name} | {date_str}"
