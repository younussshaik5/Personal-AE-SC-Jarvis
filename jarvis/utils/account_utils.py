#!/usr/bin/env python3
"""Account path utility — safe extraction of account name from any path."""

from pathlib import Path
from typing import Optional


def extract_account_name(path: Path, accounts_dir: Path) -> Optional[str]:
    """
    Extract account name from a file path.
    Returns None if the path is not inside a valid account folder.
    """
    try:
        rel = path.resolve().relative_to(accounts_dir.resolve())
    except ValueError:
        return None

    if not rel.parts:
        return None

    candidate = rel.parts[0]

    # Must be a direct child of ACCOUNTS/ and must be an existing directory
    account_path = accounts_dir / candidate
    if not account_path.is_dir():
        return None

    # Exclude known non-account system folders (if any)
    # (These shouldn't exist as folders under ACCOUNTS/, but just in case)
    system_folders = {'.git', '__pycache__', 'MEMORY', 'data', 'logs', 'recordings', 'DOCUMENTS', 'EMAILS', 'MEETINGS'}
    if candidate in system_folders:
        return None

    return candidate
