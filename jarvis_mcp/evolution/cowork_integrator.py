import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

class CoworkIntegrator:
    def __init__(self, account_path: str):
        self.account_path = Path(account_path)
        self.cowork_uploads_dir = self.account_path / ".cowork_uploads"
        self.cowork_uploads_dir.mkdir(exist_ok=True)
        self.cowork_log = self.account_path / ".cowork_integrations.json"

        if not self.cowork_log.exists():
            with open(self.cowork_log, "w") as f:
                json.dump({"integrations": []}, f, indent=2)

    async def process_cowork_upload(self, file_path: str, file_name: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        result = {
            "timestamp": datetime.now().isoformat(),
            "file_name": file_name,
            "file_path": file_path,
            "status": "processing",
            "action_taken": None,
            "destination": None
        }

        try:
            source_path = Path(file_path)
            if not source_path.exists():
                result["status"] = "error"
                result["action_taken"] = "File not found"
                self._log_integration(result)
                return result

            destination = await self._determine_destination(file_name, context)
            if destination:
                dest_path = self.account_path / destination
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, dest_path)
                result["status"] = "success"
                result["action_taken"] = f"Copied to {destination}"
                result["destination"] = str(dest_path)
            else:
                result["status"] = "skipped"
                result["action_taken"] = "No matching destination"

        except Exception as e:
            result["status"] = "error"
            result["action_taken"] = str(e)

        self._log_integration(result)
        return result

    async def _determine_destination(self, file_name: str, context: Dict[str, Any] = None) -> str:
        """Determine destination based on file type."""
        file_lower = file_name.lower()

        if "proposal" in file_lower:
            return "proposal.pdf"
        elif "rfi" in file_lower:
            return "rfi.json"
        elif "discovery" in file_lower:
            return "discovery.md"
        elif file_lower.endswith((".pdf", ".doc", ".docx")):
            return f"documents/{file_name}"
        elif file_lower.endswith((".xlsx", ".xls", ".csv")):
            return f"data/{file_name}"
        else:
            return f"documents/{file_name}"

    def _log_integration(self, result: Dict[str, Any]):
        try:
            with open(self.cowork_log, "r") as f:
                log = json.load(f)
        except:
            log = {"integrations": []}

        log["integrations"].append(result)
        log["last_integration"] = datetime.now().isoformat()

        if len(log["integrations"]) > 500:
            log["integrations"] = log["integrations"][-500:]

        try:
            with open(self.cowork_log, "w") as f:
                json.dump(log, f, indent=2)
        except:
            pass

    async def get_integrator_status(self) -> Dict[str, Any]:
        try:
            with open(self.cowork_log, "r") as f:
                log = json.load(f)
        except:
            log = {"integrations": []}

        return {
            "integrator_ready": True,
            "total_integrations": len(log.get("integrations", [])),
            "successful_integrations": len([i for i in log.get("integrations", []) if i.get("status") == "success"]),
            "last_integration": log.get("last_integration", "Never")
        }
