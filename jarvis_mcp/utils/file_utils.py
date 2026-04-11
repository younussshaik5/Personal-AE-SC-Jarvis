"""File utilities for JARVIS."""

import asyncio
from pathlib import Path


async def read_file(path: Path) -> str:
    """Read file content asynchronously."""
    try:
        loop = asyncio.get_event_loop()
        # run_in_executor only accepts positional args — use a lambda to pass encoding
        return await loop.run_in_executor(None, lambda: path.read_text(encoding='utf-8', errors='replace'))
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return ""


async def write_file(path: Path, content: str) -> bool:
    """Write file content asynchronously."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: path.write_text(content, encoding='utf-8'))
        return True
    except Exception as e:
        print(f"Error writing {path}: {e}")
        return False
