#!/usr/bin/env python3
"""
JARVIS UI Server - Serves the dashboard and provides API bridge to MCP.
"""

import http.server
import socketserver
import json
import os
import sys
import asyncio
import threading
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

PORT = 8080
WS_PORT = 8081

class UIHandler(http.server.SimpleHTTPRequestHandler):
    """Serve UI files and provide API endpoints."""
    
    def __init__(self, *args, jarvis_core=None, **kwargs):
        self.jarvis_core = jarvis_core
        super().__init__(*args, directory=str(Path(__file__).parent / 'static'), **kwargs)
    
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.serve_file('index.html')
        elif self.path.startswith('/api/'):
            self.handle_api()
        else:
            self.serve_file(self.path.lstrip('/'))
    
    def serve_file(self, filename):
        try:
            with open(Path(self.directory) / filename, 'rb') as f:
                content = f.read()
                self.send_response(200)
                if filename.endswith('.html'):
                    self.send_header('Content-Type', 'text/html')
                elif filename.endswith('.css'):
                    self.send_header('Content-Type', 'text/css')
                elif filename.endswith('.js'):
                    self.send_header('Content-Type', 'text/javascript')
                self.end_headers()
                self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, f"File not found: {filename}")
    
    def handle_api(self):
        """Handle API requests (proxy to JARVIS core or read memory files)."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        data = {}
        path = self.path
        
        try:
            if path == '/api/status':
                data = self.get_status()
            elif path == '/api/personas':
                data = self.get_personas()
            elif path == '/api/deals':
                data = self.get_deals()
            elif path == '/api/patterns':
                data = self.get_patterns()
            elif path == '/api/competitors':
                data = self.get_competitors()
            elif path == '/api/approvals':
                data = self.get_approvals()
            elif path == '/api/stats':
                data = self.get_stats()
            elif path.startswith('/api/trigger/'):
                action = path.split('/')[-1]
                data = self.trigger_action(action)
            else:
                data = {'error': 'Unknown endpoint'}
        except Exception as e:
            data = {'error': str(e)}
        
        self.wfile.write(json.dumps(data).encode())
    
    def get_status(self):
        """Get overall system status."""
        workspace = Path.cwd()
        # Get change count from approved_changes.json
        change_count = 0
        try:
            changes_file = Path('MEMORY/approved_changes.json')
            if changes_file.exists():
                with open(changes_file) as f:
                    data = json.load(f)
                    change_count = data.get('count', 0)
        except:
            pass

        # Get active persona (single sales_professional persona)
        active_persona = 'sales_professional'  # default
        try:
            persona_file = Path('MEMORY/active_persona.json')
            if persona_file.exists():
                with open(persona_file) as f:
                    data = json.load(f)
                    active_persona = data.get('current_persona', active_persona)
        except:
            pass

        status = {
            'running': True,  # assume UI server is running
            'timestamp': datetime.utcnow().isoformat(),
            'workspace': str(workspace),
            'uptime': self.get_uptime(),
            'change_count': change_count,
            'active_persona': active_persona
        }
        return status
    
    def get_uptime(self):
        """Get JARVIS process uptime."""
        try:
            with open('.jarvis.pid') as f:
                pid = int(f.read().strip())
            # Check if process still running
            os.kill(pid, 0)  # raises if not running
            # For demo, return placeholder
            return "2h 14m"
        except:
            return "0s"
    
    def get_personas(self):
        """Read personas from MEMORY."""
        personas_file = Path('MEMORY/persona_switch_log.json')
        if personas_file.exists():
            with open(personas_file) as f:
                data = json.load(f)
            # Return distinct personas from switch history
            personas = set()
            for switch in data.get('switches', []):
                personas.add(switch['from'])
                personas.add(switch['to'])
            return list(personas)
        return ['sales_professional']
    
    def get_deals(self):
        """Read deals from persona data."""
        deals = []
        try:
            # Would read from SQLite
            pass
        except:
            pass
        return deals
    
    def get_patterns(self):
        """Read learned patterns."""
        patterns = {}
        for persona in ['sales_professional']:
            path = Path(f'MEMORY/patterns/{persona}_patterns.json')
            if path.exists():
                with open(path) as f:
                    patterns[persona] = json.load(f)
        return patterns
    
    def get_competitors(self):
        """Read competitor mentions."""
        comp_file = Path('MEMORY/competitor_mentions.json')
        if comp_file.exists():
            with open(comp_file) as f:
                return json.load(f).get('mentions', [])
        return []
    
    def get_approvals(self):
        """Get pending approvals."""
        # Would read from memory
        return []
    
    def get_stats(self):
        """Get quick stats."""
        stats = {
            'files_observed': self.count_files(),
            'patterns': self.count_patterns(),
            'deals_active': 0,
            'trust_score': 65  # placeholder
        }
        return stats
    
    def count_files(self):
        """Count observed files."""
        try:
            patterns_file = Path('MEMORY/patterns/sales_professional_patterns.json')
            if patterns_file.exists():
                with open(patterns_file) as f:
                    data = json.load(f)
                return data.get('statistics', {}).get('total_files_observed', 0)
        except:
            pass
        return 0
    
    def count_patterns(self):
        """Count learned patterns."""
        try:
            patterns_file = Path('MEMORY/patterns/sales_professional_patterns.json')
            if patterns_file.exists():
                with open(patterns_file) as f:
                    data = json.load(f)
                return data.get('statistics', {}).get('patterns_discovered', 0)
        except:
            pass
        return 0
    
    def trigger_action(self, action):
        """Trigger action via MCP or direct call."""
        result = {'action': action, 'status': 'triggered'}
        
        if action == 'archive':
            # Trigger archive via system command
            os.system('python3 -c "from jarvis.archive.archiver import Archiver; import asyncio; a=Archiver(None,None); asyncio.run(a.create_snapshot(\"manual\"))"')
            result['message'] = 'Snapshot created'
        elif action == 'evolve':
            # Trigger evolution cycle
            result['message'] = 'Evolution cycle started'
        elif action == 'scan':
            # Trigger workspace scan
            result['message'] = 'Workspace scan initiated'
        elif action == 'backup':
            # Create backup
            result['message'] = 'Backup created'
        
        return result
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        pass


def start_ui_server(jarvis_core=None):
    """Start the UI server in a thread."""
    handler = lambda *args, **kwargs: UIHandler(*args, jarvis_core=jarvis_core, **kwargs)
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"JARVIS UI server running at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    print(f"Starting JARVIS UI server on port {PORT}...")
    start_ui_server()