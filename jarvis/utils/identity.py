#!/usr/bin/env python3
"""JARVIS Identity Module - Provides consistent SE identity across all components."""

from dataclasses import dataclass
from typing import Optional
from jarvis.utils.config import ConfigManager


@dataclass
class ProfessionalIdentity:
    """Professional identity information (Sales or Presales)."""
    name: str
    initials: str
    title: str
    role: str
    full_display: str
    signature: str


def get_professional_identity(config_manager: Optional[ConfigManager] = None) -> ProfessionalIdentity:
    """Get the configured professional identity.
    
    Args:
        config_manager: Optional ConfigManager instance. If None, creates one.
    
    Returns:
        ProfessionalIdentity object with name, initials, title, role, etc.
    """
    if config_manager is None:
        config_manager = ConfigManager()
        config_manager.load()
    
    # Try the new 'identity' key first
    identity_config = getattr(config_manager.config, 'identity', None)
    if not identity_config:
        # Fallback to old 'solution_engineer' for backward compatibility during transition
        identity_config = getattr(config_manager.config, 'solution_engineer', None)
        
    if identity_config:
        name = getattr(identity_config, 'name', 'YOUR_NAME')
        initials = getattr(identity_config, 'initials', 'XY')
        title = getattr(identity_config, 'title', 'Professional')
        role = getattr(identity_config, 'role', 'Sales & Presales')
    else:
        # Fallback defaults
        name = 'YOUR_NAME'
        initials = 'XY'
        title = 'Professional'
        role = 'Sales & Presales'
    
    full_display = f"{initials} {name}"
    signature = f"{initials} {name}"
    
    return ProfessionalIdentity(
        name=name,
        initials=initials,
        title=title,
        role=role,
        full_display=full_display,
        signature=signature
    )


def format_identity_signature(date: Optional[str] = None, include_title: bool = True) -> str:
    """Get a formatted professional signature for file headers.

    Args:
        date: Optional date string. If None, uses current date.
        include_title: Whether to include the title.

    Returns:
        Formatted signature string.
    """
    from datetime import datetime
    identity = get_professional_identity()
    date_str = date or datetime.now().strftime("%Y-%m-%d")

    if include_title:
        return f"{identity.initials} {identity.name} | {identity.title} | {date_str}"
    return f"{identity.initials} {identity.name} | {date_str}"


# Backward compatibility alias
get_se_identity = get_professional_identity
