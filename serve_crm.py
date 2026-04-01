#!/usr/bin/env python3
"""
JARVIS CRM Dashboard Server
Serves the interactive CRM dashboard with real data from ACCOUNTS folder
Run: python3 serve_crm.py
"""

import json
import os
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import webbrowser
import time

# Find ACCOUNTS folder - look in parent and current directory
script_dir = Path(__file__).parent
ACCOUNTS_ROOT = script_dir / "ACCOUNTS"
if not ACCOUNTS_ROOT.exists():
    # Try looking in parent directory (~/Documents/claude space/ACCOUNTS)
    ACCOUNTS_ROOT = script_dir.parent / "ACCOUNTS"
if not ACCOUNTS_ROOT.exists():
    # Fallback to absolute path
    ACCOUNTS_ROOT = Path.home() / "Documents" / "claude space" / "ACCOUNTS"

class CRMHandler(SimpleHTTPRequestHandler):
    """HTTP handler for CRM dashboard"""

    def do_GET(self):
        """Handle GET requests"""
        # API endpoint: /api/accounts
        if self.path == "/api/accounts":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            accounts_data = load_accounts_data()
            self.wfile.write(json.dumps(accounts_data).encode())
            return

        # Serve crm.html for root
        if self.path == "/" or self.path == "":
            try:
                crm_file = Path(__file__).parent / "crm.html"
                with open(crm_file, 'r') as f:
                    self.send_response(200)
                    self.send_header("Content-type", "text/html")
                    self.end_headers()
                    self.wfile.write(f.read().encode())
                return
            except:
                self.send_error(404)
                return

        # Try to serve other files from script directory
        try:
            file_path = Path(__file__).parent / self.path.lstrip('/')
            if file_path.exists() and file_path.is_file():
                with open(file_path, 'rb') as f:
                    self.send_response(200)
                    if str(file_path).endswith('.html'):
                        self.send_header("Content-type", "text/html")
                    elif str(file_path).endswith('.js'):
                        self.send_header("Content-type", "application/javascript")
                    elif str(file_path).endswith('.css'):
                        self.send_header("Content-type", "text/css")
                    elif str(file_path).endswith('.json'):
                        self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(f.read())
                return
        except:
            pass

        self.send_error(404)

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def load_accounts_data():
    """Load all accounts and deals from ACCOUNTS folder"""
    accounts = []
    deals = []
    contacts = []

    if not ACCOUNTS_ROOT.exists():
        return {"accounts": [], "deals": [], "contacts": []}

    # Scan all account folders
    for account_folder in ACCOUNTS_ROOT.iterdir():
        if not account_folder.is_dir() or account_folder.name.startswith('.'):
            continue

        account_name = account_folder.name
        account_data = load_account(account_folder, account_name)

        if account_data:
            accounts.append(account_data)

            # Load sub-accounts (like Tata/TataSky)
            for sub_folder in account_folder.iterdir():
                if sub_folder.is_dir() and not sub_folder.name.startswith('.'):
                    sub_account_name = f"{account_name}/{sub_folder.name}"
                    sub_data = load_account(sub_folder, sub_account_name, parent=account_name)
                    if sub_data:
                        accounts.append(sub_data)

    return {
        "accounts": accounts,
        "deals": deals,
        "contacts": contacts
    }


def load_account(folder_path, account_name, parent=None):
    """Load a single account's data"""
    deal_stage_file = folder_path / "deal_stage.json"
    company_research_file = folder_path / "company_research.md"

    if not deal_stage_file.exists():
        return None

    # Read deal_stage.json
    try:
        with open(deal_stage_file, 'r') as f:
            deal_data = json.load(f)
    except:
        return None

    # Read company_research.md if exists
    company_info = ""
    if company_research_file.exists():
        try:
            with open(company_research_file, 'r') as f:
                company_info = f.read()
        except:
            pass

    # Extract account info from deal_stage.json
    account_obj = {
        "id": account_name.lower().replace("/", "_").replace(" ", "_"),
        "name": deal_data.get("account_name", account_name),
        "path": str(folder_path),
        "parent": parent,
        "stage": deal_data.get("stage", "Unknown"),
        "probability": deal_data.get("probability", 0),
        "deal_size": deal_data.get("deal_size", 0),
        "timeline": deal_data.get("timeline", "TBD"),
        "stakeholders": deal_data.get("stakeholders", []),
        "competitive_situation": deal_data.get("competitive_situation", {}),
        "company_info": company_info[:500] if company_info else "No company information",
        "activities": deal_data.get("activities", []),
        "last_updated": deal_data.get("last_updated", "Unknown")
    }

    return account_obj


def start_server(port=8000):
    """Start the CRM server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, CRMHandler)

    print(f"")
    print(f"╔════════════════════════════════════════════════╗")
    print(f"║     🤖 JARVIS CRM Dashboard Server Started     ║")
    print(f"╚════════════════════════════════════════════════╝")
    print(f"")
    print(f"📊 Dashboard: http://localhost:{port}")
    print(f"📁 ACCOUNTS:  {ACCOUNTS_ROOT}")
    print(f"")
    print(f"Press Ctrl+C to stop the server")
    print(f"")

    # Open browser automatically
    time.sleep(1)
    webbrowser.open(f'http://localhost:{port}')

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✅ Server stopped")
        httpd.server_close()


if __name__ == "__main__":
    start_server(8000)
