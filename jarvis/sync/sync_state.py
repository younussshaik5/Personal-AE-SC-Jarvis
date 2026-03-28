"""Sync state tracking for JARVIS <-> Claude Desktop communication."""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict


@dataclass
class SyncState:
    last_sync: float = 0.0
    pending_notification_count: int = 0
    last_active_client: str = "claude_desktop"
    clients_seen: List[str] = field(default_factory=list)


def load_state(data_dir: str) -> SyncState:
    state_file = Path(data_dir) / "sync_state.json"
    try:
        if state_file.exists():
            data = json.loads(state_file.read_text())
            return SyncState(
                last_sync=data.get("last_sync", 0.0),
                pending_notification_count=data.get("pending_notification_count", 0),
                last_active_client=data.get("last_active_client", "claude_desktop"),
                clients_seen=data.get("clients_seen", [])
            )
    except Exception:
        pass
    return SyncState()


def save_state(data_dir: str, state: SyncState):
    state_file = Path(data_dir) / "sync_state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "last_sync": state.last_sync,
        "pending_notification_count": state.pending_notification_count,
        "last_active_client": state.last_active_client,
        "clients_seen": state.clients_seen,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    state_file.write_text(json.dumps(data, indent=2))
