"""Safety guard for JARVIS operations."""

from pathlib import Path


class SafetyGuard:
    """Safety guard to prevent dangerous operations."""

    def __init__(self):
        """Initialize safety guard."""
        self.killswitch_path = Path.home() / ".claude" / "jarvis.killswitch"
        self.enabled = True

    def check_killswitch(self) -> bool:
        """Check if killswitch is activated."""
        return self.killswitch_path.exists()

    def activate_killswitch(self):
        """Activate the killswitch."""
        self.killswitch_path.parent.mkdir(parents=True, exist_ok=True)
        self.killswitch_path.touch()

    def deactivate_killswitch(self):
        """Deactivate the killswitch."""
        if self.killswitch_path.exists():
            self.killswitch_path.unlink()

    def is_safe(self) -> bool:
        """Check if current operation is safe to proceed."""
        if self.check_killswitch():
            return False
        return self.enabled

    def validate_path(self, path: Path, base_path: Path) -> bool:
        """Validate that path is within base_path (prevent directory traversal)."""
        try:
            path.resolve().relative_to(base_path.resolve())
            return True
        except ValueError:
            return False
