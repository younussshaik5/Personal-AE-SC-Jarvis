"""Account Dashboard Generator - Enterprise-grade account CRM view"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)


class AccountDashboard:
    """Generates enterprise-grade HTML dashboard for accounts"""

    def __init__(self, account_path: Path):
        self.account_path = Path(account_path)
        self.account_name = account_path.name

    def generate_dashboard(self) -> str:
        """Generate comprehensive account dashboard HTML"""
        # Load account data
        deal_stage = self._load_json("deal_stage.json")
        company_research = self._load_markdown("company_research.md")
        discovery = self._load_markdown("discovery.md")
        claude_md = self._load_markdown("CLAUDE.md")

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.account_name} - JARVIS CRM</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-left: 6px solid #667eea;
        }}

        .header h1 {{
            color: #1a1a1a;
            margin-bottom: 10px;
            font-size: 32px;
            font-weight: 600;
        }}

        .header-meta {{
            display: flex;
            gap: 30px;
            margin-top: 15px;
            font-size: 14px;
        }}

        .meta-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .meta-label {{
            color: #666;
            font-weight: 500;
        }}

        .meta-value {{
            color: #1a1a1a;
            font-weight: 600;
        }}

        .status-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}

        .status-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(102, 126, 234, 0.2);
        }}

        .status-card h3 {{
            font-size: 12px;
            font-weight: 600;
            opacity: 0.9;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .status-card .value {{
            font-size: 28px;
            font-weight: bold;
        }}

        .probability-bar {{
            width: 100%;
            height: 4px;
            background: rgba(255,255,255,0.3);
            border-radius: 2px;
            margin-top: 8px;
            overflow: hidden;
        }}

        .probability-fill {{
            height: 100%;
            background: white;
            transition: width 0.3s ease;
        }}

        .main-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}

        @media (max-width: 1200px) {{
            .main-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            border-top: 4px solid #667eea;
        }}

        .card h2 {{
            color: #1a1a1a;
            margin-bottom: 15px;
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .card-content {{
            color: #555;
            line-height: 1.8;
            font-size: 14px;
        }}

        .section {{
            margin-bottom: 20px;
        }}

        .section-title {{
            color: #1a1a1a;
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            color: #667eea;
        }}

        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }}

        .info-item {{
            background: #f8f9ff;
            padding: 12px;
            border-radius: 6px;
            border-left: 3px solid #667eea;
        }}

        .info-label {{
            font-size: 12px;
            color: #666;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 4px;
        }}

        .info-value {{
            font-size: 16px;
            color: #1a1a1a;
            font-weight: 600;
        }}

        .timeline {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .timeline-item {{
            padding: 12px;
            background: #f8f9ff;
            border-left: 3px solid #667eea;
            border-radius: 4px;
        }}

        .timeline-date {{
            font-size: 12px;
            color: #667eea;
            font-weight: 600;
        }}

        .timeline-text {{
            font-size: 14px;
            color: #1a1a1a;
            margin-top: 4px;
        }}

        .risk-high {{
            color: #e74c3c;
            font-weight: 600;
        }}

        .risk-medium {{
            color: #f39c12;
            font-weight: 600;
        }}

        .risk-low {{
            color: #27ae60;
            font-weight: 600;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-right: 8px;
            margin-bottom: 8px;
        }}

        .badge-stage {{
            background: #e8f0ff;
            color: #667eea;
        }}

        .badge-status {{
            background: #e8f5e9;
            color: #27ae60;
        }}

        .footer {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            margin-top: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        .footer-brand {{
            font-weight: 600;
            color: #667eea;
        }}

        .generated-time {{
            margin-top: 10px;
            font-size: 11px;
            color: #999;
        }}

        .progress-bar {{
            width: 100%;
            height: 6px;
            background: #e0e0e0;
            border-radius: 3px;
            overflow: hidden;
            margin-top: 8px;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            transition: width 0.3s ease;
        }}

        .empty-state {{
            text-align: center;
            padding: 40px;
            color: #999;
        }}

        .empty-state-icon {{
            font-size: 48px;
            margin-bottom: 15px;
        }}

        .link-button {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            font-size: 13px;
            margin-top: 15px;
            display: inline-block;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📊 {deal_stage.get('account_name', self.account_name)}</h1>
            <div class="header-meta">
                <div class="meta-item">
                    <span class="meta-label">Stage:</span>
                    <span class="meta-value">{deal_stage.get('stage', 'Unknown')}</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Status:</span>
                    <span class="badge badge-status">Active</span>
                </div>
                <div class="meta-item">
                    <span class="meta-label">Updated:</span>
                    <span class="meta-value">{deal_stage.get('last_updated', 'N/A')}</span>
                </div>
            </div>

            <!-- Status Cards -->
            <div class="status-grid">
                <div class="status-card">
                    <h3>Win Probability</h3>
                    <div class="value">{deal_stage.get('probability', 0)}%</div>
                    <div class="probability-bar">
                        <div class="probability-fill" style="width: {deal_stage.get('probability', 0)}%"></div>
                    </div>
                </div>
                <div class="status-card">
                    <h3>Deal Size</h3>
                    <div class="value">${deal_stage.get('deal_size', 0):,.0f}</div>
                </div>
                <div class="status-card">
                    <h3>Timeline</h3>
                    <div class="value">{deal_stage.get('timeline', 'TBD')}</div>
                </div>
                <div class="status-card">
                    <h3>Stakeholders</h3>
                    <div class="value">{len(deal_stage.get('stakeholders', []))}</div>
                </div>
            </div>
        </div>

        <!-- Main Content Grid -->
        <div class="main-grid">
            <!-- Company Overview -->
            <div class="card">
                <h2>🏢 Company Overview</h2>
                <div class="card-content">
                    {self._extract_company_info(company_research)}
                    <a href="company_research.md" class="link-button">→ View Full Research</a>
                </div>
            </div>

            <!-- Deal Information -->
            <div class="card">
                <h2>💼 Deal Information</h2>
                <div class="card-content">
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Deal Size</div>
                            <div class="info-value">${deal_stage.get('deal_size', 0):,.0f}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Probability</div>
                            <div class="info-value">{deal_stage.get('probability', 0)}%</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Current Stage</div>
                            <div class="info-value">{deal_stage.get('stage', 'Unknown')}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Timeline</div>
                            <div class="info-value">{deal_stage.get('timeline', 'TBD')}</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Discovery Notes -->
            <div class="card">
                <h2>🔍 Discovery Insights</h2>
                <div class="card-content">
                    {self._extract_discovery_info(discovery)}
                    <a href="discovery.md" class="link-button">→ View Full Discovery Notes</a>
                </div>
            </div>

            <!-- Stakeholders -->
            <div class="card">
                <h2>👥 Stakeholders</h2>
                <div class="card-content">
                    {self._render_stakeholders(deal_stage.get('stakeholders', []))}
                </div>
            </div>

            <!-- Activities -->
            <div class="card">
                <h2>📅 Recent Activities</h2>
                <div class="card-content">
                    {self._render_activities(deal_stage.get('activities', []))}
                </div>
            </div>

            <!-- Next Milestone -->
            <div class="card">
                <h2>🎯 Next Milestone</h2>
                <div class="card-content">
                    {self._render_next_milestone(deal_stage.get('next_milestone', {}))}
                </div>
            </div>

            <!-- Competitive Situation -->
            <div class="card">
                <h2>⚔️ Competitive Situation</h2>
                <div class="card-content">
                    {self._render_competitive(deal_stage.get('competitive_situation', {}))}
                </div>
            </div>

            <!-- Account Settings -->
            <div class="card">
                <h2>⚙️ Account Settings</h2>
                <div class="card-content">
                    <div class="section">
                        <div class="section-title">Model Preferences</div>
                        <p>Account-specific AI model settings configured in CLAUDE.md</p>
                    </div>
                    <div class="section">
                        <div class="section-title">Auto-Evolution</div>
                        <p>CLAUDE.md learns from interactions and auto-improves</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="footer-brand">✨ JARVIS CRM Dashboard</div>
            <div class="generated-time">Last generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC</div>
            <div class="generated-time">Auto-refreshes from account files</div>
        </div>
    </div>
</body>
</html>
"""
        return html

    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Load JSON file from account"""
        try:
            file_path = self.account_path / filename
            if file_path.exists():
                return json.loads(file_path.read_text())
        except Exception as e:
            logger.warning(f"Error loading {filename}: {e}")
        return {}

    def _load_markdown(self, filename: str) -> str:
        """Load markdown file from account"""
        try:
            file_path = self.account_path / filename
            if file_path.exists():
                return file_path.read_text()
        except Exception as e:
            logger.warning(f"Error loading {filename}: {e}")
        return ""

    def _extract_company_info(self, content: str) -> str:
        """Extract company info summary from markdown"""
        lines = content.split("\n")
        info_lines = []

        for line in lines[1:11]:  # First 10 lines after title
            if line.strip() and not line.startswith("#"):
                info_lines.append(f"<p>{line.strip()}</p>")

        return "\n".join(info_lines) if info_lines else "<p>No company info yet.</p>"

    def _extract_discovery_info(self, content: str) -> str:
        """Extract discovery summary from markdown"""
        lines = content.split("\n")
        info_lines = []

        for line in lines[1:8]:  # First few lines
            if line.strip() and not line.startswith("#"):
                info_lines.append(f"<p>{line.strip()}</p>")

        return "\n".join(info_lines) if info_lines else "<p>No discovery info yet.</p>"

    def _render_stakeholders(self, stakeholders: list) -> str:
        """Render stakeholders list"""
        if not stakeholders:
            return "<p>No stakeholders added yet.</p>"

        html = '<div class="timeline">'
        for stakeholder in stakeholders[:5]:  # Show first 5
            name = stakeholder.get("name", "Unknown")
            title = stakeholder.get("title", "")
            html += f"""
            <div class="timeline-item">
                <div class="timeline-text"><strong>{name}</strong></div>
                <div class="info-label">{title}</div>
            </div>
            """
        html += "</div>"
        return html

    def _render_activities(self, activities: list) -> str:
        """Render activities timeline"""
        if not activities:
            return "<p>No activities recorded yet.</p>"

        html = '<div class="timeline">'
        for activity in activities[-5:]:  # Show last 5
            date = activity.get("date", "N/A")
            activity_type = activity.get("type", "Unknown")
            html += f"""
            <div class="timeline-item">
                <div class="timeline-date">{date}</div>
                <div class="timeline-text">{activity_type}</div>
            </div>
            """
        html += "</div>"
        return html

    def _render_next_milestone(self, milestone: dict) -> str:
        """Render next milestone"""
        if not milestone:
            return "<p>No milestone set yet.</p>"

        date = milestone.get("date", "TBD")
        activity = milestone.get("activity", "TBD")
        description = milestone.get("description", "")

        return f"""
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Date</div>
                <div class="info-value">{date}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Activity</div>
                <div class="info-value">{activity}</div>
            </div>
        </div>
        <p style="margin-top: 12px; color: #666;">{description}</p>
        """

    def _render_competitive(self, competitive: dict) -> str:
        """Render competitive information"""
        if not competitive:
            return "<p>No competitive info yet.</p>"

        competitor = competitive.get("primary_competitor", "TBD")
        status = competitive.get("competitor_status", "Unknown")
        our_price = competitive.get("our_price", "TBD")
        win_prob = competitive.get("win_probability_vs_competitor", 0)

        return f"""
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">Primary Competitor</div>
                <div class="info-value">{competitor}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Status</div>
                <div class="info-value">{status}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Our Price</div>
                <div class="info-value">{our_price}</div>
            </div>
            <div class="info-item">
                <div class="info-label">Win Probability</div>
                <div class="info-value">{win_prob}%</div>
            </div>
        </div>
        """
