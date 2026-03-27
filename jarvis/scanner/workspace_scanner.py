#!/usr/bin/env python3
"""
Workspace Scanner - Analyzes workspace structure and technology stack.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass, field, asdict
from jarvis.utils.logger import JARVISLogger
from jarvis.utils.event_bus import EventBus, Event


@dataclass
class WorkspaceProfile:
    """Profile of a workspace analysis."""
    workspace_path: str
    project_type: str = "unknown"
    file_counts: Dict[str, int] = field(default_factory=dict)
    total_files: int = 0
    total_dirs: int = 0
    languages: Dict[str, int] = field(default_factory=dict)
    frameworks: List[str] = field(default_factory=list)
    entry_points: List[str] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    git_repos: List[str] = field(default_factory=list)
    scanned_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WorkspaceScanner:
    """Scans workspace to detect tech stack and structure."""

    # Language detection by file extension
    LANGUAGE_EXTENSIONS = {
        'python': ['.py', '.pyw', '.pyi'],
        'javascript': ['.js', '.jsx', '.mjs'],
        'typescript': ['.ts', '.tsx'],
        'java': ['.java', '.jar'],
        'go': ['.go'],
        'rust': ['.rs'],
        'cpp': ['.cpp', '.cc', '.cxx', '.c++'],
        'c': ['.c', '.h'],
        'ruby': ['.rb'],
        'php': ['.php'],
        'swift': ['.swift'],
        'kotlin': ['.kt'],
        'scala': ['.scala'],
        'html': ['.html', '.htm'],
        'css': ['.css', '.scss', '.sass', '.less'],
        'json': ['.json'],
        'yaml': ['.yaml', '.yml'],
        'xml': ['.xml'],
        'markdown': ['.md', '.markdown'],
        'shell': ['.sh', '.bash', '.zsh'],
        'sql': ['.sql'],
        'dockerfile': ['Dockerfile'],
        'makefile': ['Makefile', 'makefile'],
    }

    # Framework indicators (files or directories that signal a framework)
    FRAMEWORK_INDICATORS = {
        'react': ['package.json:react', 'node_modules/react'],
        'vue': ['package.json:vue', 'node_modules/vue'],
        'angular': ['package.json:@angular/core', 'angular.json'],
        'django': ['manage.py', 'settings.py'],
        'flask': ['app.py', 'flask_app.py'],
        'fastapi': ['main.py:FastAPI', 'app.py:FastAPI'],
        'express': ['package.json:express', 'app.js:express'],
        'spring': ['pom.xml:spring', 'build.gradle:spring'],
        'rails': ['Gemfile:rails', 'config/routes.rb'],
        'laravel': ['artisan', 'composer.json:laravel'],
        'nextjs': ['next.config.js', 'pages/'],
        'nuxt': ['nuxt.config.js'],
        'gatsby': ['gatsby-config.js'],
        'react_native': ['package.json:react-native'],
        'flutter': ['pubspec.yaml:flutter', 'lib/main.dart'],
        'unity': ['ProjectSettings/ProjectSettings.asset'],
        'unreal': ['*.uproject'],
    }

    def __init__(self, config, event_bus: EventBus):
        self.config = config
        self.event_bus = event_bus
        self.logger = JARVISLogger("scanner")
        self._workspace_root: Path = config.workspace_root
        self._running = False

        # Subscribe to scan requests
        self.event_bus.subscribe("scan.requested", self._on_scan_requested)

    async def start(self):
        """Start the scanner (registers event handlers)."""
        self.logger.info("Workspace scanner started", workspace=str(self._workspace_root))
        self._running = True

    async def stop(self):
        """Stop the scanner."""
        self._running = False
        self.logger.info("Workspace scanner stopped")

    def _on_scan_requested(self, event: Event):
        """Handle a scan request."""
        asyncio.create_task(self.scan_and_report(reason=event.data.get('reason', 'manual')))

    async def scan_and_report(self, reason: str = "manual") -> WorkspaceProfile:
        """Perform a full workspace scan and publish results."""
        self.logger.info("Starting workspace scan", reason=reason)
        profile = await self.scan_workspace()
        
        # Publish event
        self.event_bus.publish(Event("workspace.scanned", "scanner", {
            "profile": profile.to_dict(),
            "reason": reason,
            "workspace": str(self._workspace_root)
        }))
        
        self.logger.info("Workspace scan completed",
                        total_files=profile.total_files,
                        languages=list(profile.languages.keys()))
        return profile

    async def scan_workspace(self) -> WorkspaceProfile:
        """Scan the workspace and return a profile."""
        profile = WorkspaceProfile(
            workspace_path=str(self._workspace_root),
            scanned_at=asyncio.get_event_loop().time()
        )

        try:
            # Walk the workspace (but ignore some directories)
            ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.idea', '.vscode', 'dist', 'build', 'target', 'bin', 'obj'}
            
            for root, dirs, files in self._workspace_root.walk():
                # Skip ignored directories
                dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
                
                # Count directories
                profile.total_dirs += 1
                
                # Process files
                for file in files:
                    ext = Path(file).suffix.lower()
                    profile.total_files += 1
                    
                    # Count by extension
                    file_type = ext.lstrip('.') if ext else 'no_extension'
                    profile.file_counts[file_type] = profile.file_counts.get(file_type, 0) + 1
                    
                    # Detect language
                    for lang, exts in self.LANGUAGE_EXTENSIONS.items():
                        if ext in exts:
                            profile.languages[lang] = profile.languages.get(lang, 0) + 1
                            break

            # Detect entry points and frameworks (basic heuristics)
            await self._detect_entry_points(profile)
            await self._detect_frameworks(profile)
            await self._detect_dependencies(profile)

        except Exception as e:
            self.logger.error("Error during scan", error=str(e))

        return profile

    async def _detect_entry_points(self, profile: WorkspaceProfile):
        """Detect common entry point files."""
        entry_patterns = [
            'main.py', 'app.py', 'index.js', 'index.ts', 'main.js', 'main.ts',
            'server.js', 'server.ts', 'manage.py', 'Makefile', 'Dockerfile',
            'package.json', 'pom.xml', 'build.gradle', 'Cargo.toml'
        ]
        for pattern in entry_patterns:
            matches = list(self._workspace_root.rglob(pattern))
            if matches:
                profile.entry_points.append(pattern)

    async def _detect_frameworks(self, profile: WorkspaceProfile):
        """Detect frameworks based on indicator files."""
        detected = set()
        for framework, indicators in self.FRAMEWORK_INDICATORS.items():
            for indicator in indicators:
                # Indicator can be "file:content" or "path"
                if ':' in indicator:
                    file_pattern, content_keyword = indicator.split(':', 1)
                    matches = list(self._workspace_root.rglob(file_pattern))
                    for match in matches:
                        try:
                            with open(match, 'r', encoding='utf-8', errors='ignore') as f:
                                if content_keyword in f.read():
                                    detected.add(framework)
                                    break
                        except:
                            pass
                else:
                    matches = list(self._workspace_root.rglob(indicator))
                    if matches:
                        detected.add(framework)
        profile.frameworks = list(detected)

    async def _detect_dependencies(self, profile: WorkspaceProfile):
        """Parse common dependency files."""
        # Python
        requirements_files = self._workspace_root.glob('requirements.txt')
        for req_file in requirements_files:
            try:
                with open(req_file) as f:
                    deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    profile.dependencies['python'] = deps[:20]  # limit
            except:
                pass

        # Node.js
        package_json = self._workspace_root / 'package.json'
        if package_json.exists():
            try:
                import json
                with open(package_json) as f:
                    data = json.load(f)
                deps = list(data.get('dependencies', {}).keys()) + list(data.get('devDependencies', {}).keys())
                profile.dependencies['javascript'] = deps[:20]
            except:
                pass

        # Java Maven
        pom_xml = self._workspace_root / 'pom.xml'
        if pom_xml.exists():
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(pom_xml)
                root = tree.getroot()
                # Look for groupId/artifactId (simplified)
                deps = []
                for dep in root.findall('.//dependency'):
                    gid = dep.find('groupId')
                    aid = dep.find('artifactId')
                    if gid is not None and aid is not None:
                        deps.append(f"{gid.text}:{aid.text}")
                profile.dependencies['java'] = deps[:20]
            except:
                pass
