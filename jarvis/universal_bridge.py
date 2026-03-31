#!/usr/bin/env python3
"""
JARVIS v3 Universal Intelligence Bridge
Real-time conversation processing across Claude Code, OpenCode, and manual inputs
Zero hard paths, universal deployment, fork-ready
"""

import os
import json
import asyncio
import threading
import shutil
from pathlib import Path
import re
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from .autodetect import UniversalWorkspaceDetector, create_platform_safe_config


@dataclass 
class ConversationContext:
    """Universal conversation context for real-time processing"""
    source: str  # 'claude_codec', 'claude_cowork', 'opencode', 'manual'
    text: str
    timestamp: float
    workspace: str
    account_context: Optional[str] = None
    detected_skills: List[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class AccountResolve:
    """Account resolution result"""
    account_name: str
    confidence: float
    methods: List[str]
    files: List[str] = None


class RealtimeBridge:
    """Universal real-time intelligence processing bridge"""
    
    def __init__(self, workspace_root: str = None):
        self.detector = UniversalWorkspaceDetector()
        self.context = self.detector.get_workspace_context()
        self.workspace_root = Path(workspace_root) if workspace_root else self.context.root
        
        # Real-time file watchers
        self.watch_threads = {}
        self.processing_active = False
        
        # Account mapping cache
        self.account_cache = {}
        self.skill_map = {}
        
        # Universal registration
        self.universal_sources = {
            'claude_codec': self.path_claude_codec,
            'claude_cowork': self.path_claude_cowork,
            'opencode': self.path_opencode,
            'manual': self.path_manual
        }
    
    def path_claude_codec(self) -> Path:
        """Claude Code integration path"""
        return self.workspace_root / ".claude" / "workspace.md"
    
    def path_claude_cowork(self) -> Path:
        """Claude CoWork integration path"""
        return self.workspace_root / ".lud" / "conversations.jsonl"
    
    def path_opencode(self) -> Path:
        """OpenCode integration path"""
        return self.workspace_root / ".opencode" / "conversations.md"
    
    def path_manual(self) -> Path:
        """Manual input path"""
        return self.context.javis_root / "manual" / "conversations.md"
    
    def detect_account_from_conversation(self, text: str) -> Optional[AccountResolve]:
        """Smart account detection using multiple strategies"""
        
        accounts = self.context.accounts_found
        if not accounts:
            # Auto-discover accounts from file system
            accounts = self.detector.find_account_directories()
        
        best_match = None
        best_confidence = 0.0
        methods = []
        
        for account in accounts:
            # Strategy 1: Direct name match
            if account.lower() in text.lower():
                confidence = len(account) / max(len(text), 1)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match = account
                    methods.append("direct_name_match")
            
            # Strategy 2: Company patterns
            company_patterns = re.findall(r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b', text)
            for company in company_patterns:
                if company.lower() == account.lower():
                    confidence = len(company) / max(len(account), 1)
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = account
                        methods.append("company_pattern")
        
        # Strategy 3: Email domain detection
        email_domains = re.findall(r'@([a-zA-Z0-9.-]+)', text)
        for domain in email_domains:
            domain_clean = domain.split('.')[0]
            for account in accounts:
                if domain_clean.lower() == account.lower().replace(" ", "").replace("_", ""):
                    confidence = 0.8
                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = account
                        methods.append("email_domain")
        
        if best_match:
            return AccountResolve(
                account_name=best_match,
                confidence=best_confidence,
                methods=methods
            )
        
        return None
    
    def extract_skills_from_text(self, text: str) -> List[str]:
        """Extract actionable skills from conversation"""
        skills = []
        
        # Business deal signals
        deal_patterns = [
            r"email(?:s|ing)?\s+((?:[\w.-]+@[\w.-]+|\w+))",
            r"follow\s+up(?:\swith)?\s+(.+)",
            r"meeting(?:\swith?\s+(.+))",
            r"discovery\s+call\s+with\s+(.+)",
            r"proposal\s+for\s+(.+)",
            r"demo\s+with\s+(.+)"
        ]
        
        for pattern in deal_patterns:
            matches = re.findall(pattern, text.lower(), re.IGNORECASE)
            for match in matches:
                if match:
                    skills.extend(["email_draft", "meeting_prep", "demo_setup", "proposal_create"])
        
        # Pain point detection
        pain_patterns = [
            r"(problem|issue|challenge|pain|difficulty)\s+with\s+(.+)",
            r"need\s+to\s+((?:improv|enhanc|increas|reduc|solv)\w+)\s+(.+)",
            r"(?:budget|cost|price|roi|value)\s+([A-Za-z0-9\s]+?)\b",
            r"(?:timeline|deadline|schedule)\s+([A-Za-z0-9\s]+?)\b"
        ]
        
        for pattern in pain_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                skills.extend(["pain_point_analysis", "budget_analysis", "timeline_extract"])
        
        return list(set(skills))
    
    def process_conversation(self, context: ConversationContext):
        """Process conversation in real-time"""
        
        # Account detection
        account_resolve = self.detect_account_from_conversation(context.text)
        
        # Skill extraction
        skills = self.extract_skills_from_text(context.text)
        
        # Update context
        context.account_context = account_resolve.account_name if account_resolve else None
        context.detected_skills = skills
        
        # Trigger actions
        return self.execute_realtime_actions(context, account_resolve)
    
    def execute_realtime_actions(self, context: ConversationContext, 
                               account_resolve: Optional[AccountResolve]) -> Dict[str, Any]:
        """Execute detected skills in real-time"""
        
        results = {
            "context": asdict(context),
            "actions_executed": [],
            "files_created": [],
            "account_detected": None
        }
        
        if account_resolve:
            account_name = account_resolve.account_name
            results["account_detected"] = account_name
            
            # Ensure account directory exists
            account_path = self.context.accounts_dir / account_name
            account_path.mkdir(parents=True, exist_ok=True)
            
            # Create conversation entry
            conv_file = account_path / "INTEL" / "conversations.jsonl"
            conv_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(conv_file, "a") as f:
                f.write(json.dumps(asdict(context)) + "\n")
            results["files_created"].append(str(conv_file))
            
            # Execute skills
            for skill in context.detected_skills:
                action_result = self.execute_skill(account_name, skill, context)
                if action_result:
                    results["actions_executed"].append(action_result)
        
        return results
    
    def execute_skill(self, account_name: str, skill: str, context: ConversationContext):
        """Execute specific skill action"""
        
        account_path = self.context.accounts_dir / account_name
        
        if skill == "email_draft":
            email_path = account_path / "emails" / "auto_draft.md"
            email_path.parent.mkdir(parents=True, exist_ok=True)
            
            draft = f"""# Auto-Generated Follow-up
**Account:** {account_name}
**Context:** {context.text}
**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}

---

**Subject:** Following up on {account_name} discussions

**Body:**
Based on our conversation today, I wanted to follow up regarding:
- {context.text}

Let's schedule a call to discuss next steps.

Best regards
"""
            
            with open(email_path, "w") as f:
                f.write(draft)
            
            return {"skill": skill, "file": str(email_path), "type": "generated_email"}
        
        elif skill == "meeting_prep":
            prep_path = account_path / "INTEL" / "meeting_prep.md"
            prep_path.parent.mkdir(parents=True, exist_ok=True)
            
            prep = f"""# Meeting Preparation - {account_name}
**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Source:** {context.source}
**Context:** {context.text}

### Key Points to Cover:
1. Address {context.text}
2. Next steps based on discussion
3. Timeline and expectations

### Preparation Notes:
- Review account context
- Prepare relevant materials
- Update progress tracking
"""
            
            with open(prep_path, "w") as f:
                f.write(prep)
            
            return {"skill": skill, "file": str(prep_path), "type": "meeting_prep"}
        
        elif skill == "pain_point_analysis":
            pain_path = account_path / "INTEL" / "pain_points.json"
            pain_path.parent.mkdir(parents=True, exist_ok=True)
            
            pain_points = {
                "account": account_name,
                "timestamp": context.timestamp,
                "points": [context.text],  # Full context for analysis
                "skills_triggered": [skill]
            }
            
            with open(pain_path, "a") as f:
                f.write(json.dumps(pain_points) + "\n")
            
            return {"skill": skill, "file": str(pain_path), "type": "pain_point_extract"}
        
        return {"skill": skill, "note": "handled by system"}
    
    def process_new_file(self, file_path: Path):
        """Process newly created file (watchdog event)"""
        self._process_file_event(file_path, "created")
    
    def process_modified_file(self, file_path: Path):
        """Process modified file (watchdog event)"""
        self._process_file_event(file_path, "modified")
    
    def _process_file_event(self, file_path: Path, event_type: str):
        """Common file event processing"""
        try:
            # Check if this is a new account directory creation
            if self._is_new_account_folder(file_path):
                self._initialize_account_folder(file_path)
                return
            
            # Determine source from path
            source = self._detect_source_from_path(file_path)
            
            # Only process relevant files
            if source in self.universal_sources:
                self._process_source_file(source, file_path)
        except Exception as e:
            print(f"⚠️ Error processing {event_type} {file_path}: {e}")
    
    def _is_new_account_folder(self, file_path: Path) -> bool:
        """Check if this path represents a new account folder being created"""
        try:
            # Check if path is within ACCOUNTS directory
            accounts_dir = self.context.accounts_dir
            if accounts_dir.name in file_path.parts:
                # Find the account name (first directory under ACCOUNTS)
                try:
                    idx = file_path.parts.index(accounts_dir.name)
                    if idx + 1 < len(file_path.parts):
                        account_name = file_path.parts[idx + 1]
                        account_path = accounts_dir / account_name
                        
                        # If this is the account folder itself being created
                        if file_path == account_path or file_path.parent == account_path:
                            # Check if it's a new directory (not already initialized)
                            if not (account_path / "INTEL").exists():
                                return True
                except (ValueError, IndexError):
                    pass
        except:
            pass
        return False
    
    def _initialize_account_folder(self, account_path: Path):
        """Create standard folder structure for a new account (clean minimal)"""
        try:
            account_name = account_path.name
            
            # Skip if already initialized
            if (account_path / "INTEL").exists():
                return
            
            print(f"📁 Initializing new account: {account_name}")
            
            # Create top-level folders (empty)
            top_level_folders = [
                "ARCHITECTURE",
                "BATTLECARD",
                "DEMO_STRATEGY",
                "DISCOVERY",
                "DOCUMENTS",
                "EMAILS",
                "INTEL",
                "MEETINGS",
                "NEXT_STEPS",
                "PROPOSAL",
                "RFI",
                "RISK_REPORT",
                "SOW",
                "VALUE_ARCHITECTURE"
            ]
            
            for folder in top_level_folders:
                (account_path / folder).mkdir(parents=True, exist_ok=True)
            
            # Create root files with minimal content
            root_files = {
                "lookup.md": f"# Account Profile: {account_name}\n\n**Created:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n## Basic Information\n\n## Key Contacts\n\n## Timeline\n",
                "notes.md": f"# Notes: {account_name}\n\n",
                "account.html": f"<html><head><title>{account_name}</title></head><body><h1>{account_name}</h1></body></html>",
                "actions.md": "# Actions\n\n## Next Steps\n\n## Follow-ups\n",
                "activities.jsonl": "",
                "contacts.json": "[]",
                "deal_stage.json": '{"stage": "new_account", "confidence": 0.5, "created": "' + time.strftime('%Y-%m-%d') + '"}',
                "index.json": '{"account": "' + account_name + '", "version": "3.0"}',
                "meddpicc.json": '{"score": 0, "dimensions": {}}',
                "notes.json": "[]",
                "summary.md": f"# Account Summary: {account_name}\n\n## Overview\n\n## Key Points\n"
            }
            
            for fname, content in root_files.items():
                fpath = account_path / fname
                if not fpath.exists():
                    with open(fpath, "w") as f:
                        f.write(content)
            
            # Create INTEL initial files
            intel_files = {
                "meeting_prep.md": f"# Meeting Prep: {account_name}\n\n## Current Status\n\n## Agenda Items\n\n## Preparation Notes\n",
                "pain_points.json": "[]",
                "value_architecture.md": f"# Value Architecture: {account_name}\n\n## Business Drivers\n\n## Technical Requirements\n\n## ROI Considerations\n"
            }
            
            intel_dir = account_path / "INTEL"
            for fname, content in intel_files.items():
                fpath = intel_dir / fname
                if not fpath.exists():
                    with open(fpath, "w") as f:
                        f.write(content)
            
            print(f"✅ Account '{account_name}' initialized with {len(top_level_folders)} folders + {len(root_files)} files")
            
        except Exception as e:
            print(f"⚠️ Error initializing account {account_path.name}: {e}")
            import traceback
            traceback.print_exc()
    
    def _cleanup_template_artifacts(self, account_path: Path):
        """Remove template artifacts that shouldn't be in a fresh account"""
        # Remove empty nested INTEL/INTEL folder if it exists
        nested_intel = account_path / "INTEL" / "INTEL"
        if nested_intel.exists() and nested_intel.is_dir():
            try:
                import shutil
                shutil.rmtree(nested_intel)
                print(f"   🗑️ Removed empty nested INTEL/INTEL")
            except:
                pass
    
    def _minimal_initialize(self, account_path: Path):
        """Fallback minimal initialization if template not available"""
        account_name = account_path.name
        
        # Create basic structure
        dirs = ["INTEL", "emails", "documents", "MEETINGS", "NOTES"]
        for d in dirs:
            (account_path / d).mkdir(parents=True, exist_ok=True)
        
        # Create basic files
        files = {
            "lookup.md": f"# Account Profile: {account_name}\n\n**Created:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            "notes.md": f"# Notes: {account_name}\n\n",
            "deal_stage.json": '{"stage": "new_account", "confidence": 0.5}',
            "meddpicc.json": '{"score": 0, "dimensions": {}}'
        }
        
        for fname, content in files.items():
            fpath = account_path / fname
            if not fpath.exists():
                with open(fpath, "w") as f:
                    f.write(content)
    
    def _update_account_files(self, account_path: Path, account_name: str):
        """Update account-specific files with the correct account name"""
        files_to_update = [
            "lookup.md",
            "summary.md",
            "account.html"  # HTML may have account name embedded
        ]
        
        for fname in files_to_update:
            fpath = account_path / fname
            if fpath.exists():
                try:
                    content = fpath.read_text()
                    # Replace placeholder or template account name
                    updated = content.replace("{{ACCOUNT_NAME}}", account_name)
                    updated = updated.replace("Account Name", account_name)
                    updated = updated.replace("Template Account", account_name)
                    if updated != content:
                        fpath.write_text(updated)
                except:
                    pass  # Silently skip if can't update
    
    def _check_and_initialize_account(self, dir_path: Path):
        """Check if a newly created directory is an account and initialize it"""
        try:
            accounts_dir = self.context.accounts_dir
            print(f"🔍 Checking directory: {dir_path} (parent: {dir_path.parent})")
            print(f"   ACCOUNTS dir: {accounts_dir}")
            
            # If this IS the ACCOUNTS directory itself, skip
            if dir_path.resolve() == accounts_dir.resolve():
                print(f"   → Skipping ACCOUNTS root")
                return
            
            # Check if directory is a direct child of ACCOUNTS
            if dir_path.parent.resolve() == accounts_dir.resolve():
                account_name = dir_path.name
                account_path = accounts_dir / account_name
                print(f"   → Detected new account: {account_name}")
                
                # Initialize if not already done
                if not (account_path / "INTEL").exists():
                    print(f"   → Initializing...")
                    self._initialize_account_folder(account_path)
                else:
                    print(f"   → Already initialized")
            else:
                print(f"   → Not a direct child of ACCOUNTS")
        except Exception as e:
            print(f"⚠️ Error checking account folder {dir_path}: {e}")
    
    def _detect_source_from_path(self, file_path: Path) -> Optional[str]:
        """Detect which source this file belongs to"""
        path_str = str(file_path).lower()
        
        for source, get_path in self.universal_sources.items():
            source_path = get_path()
            if str(source_path).lower() in path_str:
                return source
        
        return None
    
    def _process_source_file(self, source: str, file_path: Path):
        """Process a file for a specific source"""
        try:
            if file_path.exists():
                # Skip non-text files (images, videos, etc.)
                skip_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.tiff', '.ico',
                                 '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mp3', '.wav', '.m4a'}
                
                if file_path.suffix.lower() in skip_extensions:
                    return  # Silently skip binary files
                
                # Only process files with text extensions or common conversation formats
                allowed_extensions = {'.md', '.txt', '.json', '.jsonl', '.yaml', '.yml', '.log', '.csv'}
                if file_path.suffix.lower() and file_path.suffix.lower() not in allowed_extensions:
                    # For files without clear extension, check if they might be text
                    if not self._is_likely_text_file(file_path):
                        return
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Process each line as separate conversation
                lines = content.strip().split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 10:
                        context = ConversationContext(
                            source=source,
                            text=line,
                            timestamp=time.time(),
                            workspace=str(self.workspace_root)
                        )
                        self.process_conversation(context)
        except Exception as e:
            print(f"⚠️ Error reading {file_path}: {e}")
    
    def _is_likely_text_file(self, file_path: Path, sample_size: int = 1024) -> bool:
        """Check if a file is likely text by sampling its content"""
        try:
            with open(file_path, 'rb') as f:
                sample = f.read(sample_size)
            
            # Check for null bytes (binary indicator)
            if b'\0' in sample:
                return False
            
            # Count printable ASCII characters
            printable = sum(1 for byte in sample if 32 <= byte <= 126 or byte in [9, 10, 13])
            ratio = printable / len(sample) if sample else 0
            
            return ratio > 0.7  # 70% printable = likely text
        except:
            return False
    
    def start_realtime_monitoring(self):
        """Start real-time file system monitoring"""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class UniversalFileHandler(FileSystemEventHandler):
                def __init__(self, bridge_instance):
                    self.bridge = bridge_instance
                
                def on_created(self, event):
                    src_path = Path(event.src_path)
                    if event.is_directory:
                        # Handle new directory creation (e.g., new account folder)
                        self.bridge._check_and_initialize_account(src_path)
                    else:
                        self.bridge.process_new_file(src_path)
                
                def on_modified(self, event):
                    if not event.is_directory:
                        self.bridge.process_modified_file(Path(event.src_path))
            
            observer = Observer()
            
            # Watch universal sources (.claude, .opencode, etc.)
            for source_name, get_path_func in self.universal_sources.items():
                source_path = get_path_func()
                if source_path.parent.exists():
                    observer.schedule(
                        UniversalFileHandler(self),
                        str(source_path.parent),
                        recursive=True
                    )
            
            # Also watch ACCOUNTS directory for new account folders
            accounts_dir = self.context.accounts_dir
            if accounts_dir.exists():
                observer.schedule(
                    UniversalFileHandler(self),
                    str(accounts_dir),
                    recursive=True  # Watch all subdirectories for new account folders
                )
                print(f"👀 Watching ACCOUNTS directory: {accounts_dir}")
            
            observer.start()
            return observer
            
        except ImportError:
            # Fallback to manual polling if watchdog not available
            return self._start_manual_monitoring()
    
    def _start_manual_monitoring(self):
        """Manual file monitoring fallback"""
        def monitor_loop():
            while self.processing_active:
                self.poll_all_sources()
                time.sleep(2)
        
        thread = threading.Thread(target=monitor_loop, daemon=True)
        thread.start()
        return thread
    
    def poll_all_sources(self):
        """Manual polling of all sources"""
        for source_name, get_path_func in self.universal_sources.items():
            file_path = get_path_func()
            if file_path.exists():
                self.process_file_changes(source_name, file_path)
    
    def process_file_changes(self, source: str, file_path: Path):
        """Process changes in conversational files"""
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            for line in lines:
                if line.strip() and len(line.strip()) > 10:
                    context = ConversationContext(
                        source=source,
                        text=line.strip(),
                        timestamp=time.time(),
                        workspace=str(self.workspace_root)
                    )
                    
                    results = self.process_conversation(context)
                    
                    print(f"📡 {source}: {line[:50]}...")
                    print(f"🔍 Account: {results.get('account_detected', 'None')} | ")
                    print(f"⚡ Skills: {len(results.get('actions_executed', []))} executed")
        
        except Exception as e:
            print(f"⚠️ Error processing {source}: {e}")
    
    def run_universal_bridge(self):
        """Start universal bridge with all features"""
        
        print("🚀 JARVIS v3 Universal Intelligence Bridge Starting...")
        print(f"📁 Workspace Root: {self.workspace_root}")
        print(f"🎯 Accounts Directory: {self.context.accounts_dir}")
        print(f"🌍 Platform: {self.context.platform_name}")
        print(f"📮 Detected Accounts: {len(self.context.accounts_found)}")
        
        if self.context.accounts_found:
            for account in self.context.accounts_found:
                print(f"   ✓ {account}")
        
        print("\n🔄 Enabling real-time processing...")
        
        try:
            # Start real-time monitoring
            monitor = self.start_realtime_monitoring()
            
            # Create configuration
            config = create_platform_safe_config(self.workspace_root)
            config_path = self.context.javis_root / "config" / "universal.json"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Configuration saved to: {config_path}")
            
            # Also create .claude context
            claude_path = self.workspace_root / ".claude" / "JARVIS.md"
            claude_path.parent.mkdir(parents=True, exist_ok=True)
            
            claude_content = f"""# JARVIS Universal Intelligence Bridge
This workspace is connected to JARVIS real-time processing.
All conversations, files, and context are automatically analyzed.

**Commands:**
- Universal bridge is running in the background
- Skills update automatically as you work
- Accounts are auto-detected

**Detected Accounts:**
{'\n'.join(f'- {acc}' for acc in self.context.accounts_found) if self.context.accounts_found else 'No accounts - will create automatically'}
"""
            with open(claude_path, "w") as f:
                f.write(claude_content)
            
            print("✨ Universal bridge ready! Processing real-time conversations...")
            
            # Keep running
            try:
                self.processing_active = True
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping universal bridge...")
            
        except Exception as e:
            print(f"💥 Bridge startup error: {e}")
            print("Starting manual monitoring...")
            self.run_manual_mode()
    
    def run_manual_mode(self):
        """Fallback manual processing mode"""
        print("🔄 Manual monitoring mode activated")
        self.processing_active = True
        
        while self.processing_active:
            try:
                print(f"\n📊 Scanning conversations... {time.strftime('%H:%M:%S')}")
                self.poll_all_sources()
                time.sleep(5)  # Poll every 5 seconds
                
            except KeyboardInterrupt:
                print("\n🛑 Manual mode stopped.")
                self.processing_active = False
                break


def main(workspace_root: str = None):
    """Universal entry point"""
    bridge = RealtimeBridge(workspace_root)
    bridge.run_universal_bridge()


if __name__ == "__main__":
    import sys
    workspace = sys.argv[1] if len(sys.argv) > 1 else None
    main(workspace)