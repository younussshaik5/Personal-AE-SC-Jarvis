"""
OnboardingSkill - Interactive setup wizard for first-time users.
Intelligently probes for company and user information, auto-scaffolds account.
"""

import asyncio
from typing import Optional, Dict, Any
import logging
from pathlib import Path

from .base_skill import BaseSkill
from ..account_scaffolder import AccountScaffolder
from ..account_hierarchy import AccountHierarchy
from ..claude_md_loader import ClaudeMdLoader
from ..onboarding_info_extractor import OnboardingInfoExtractor


class OnboardingSkill(BaseSkill):
    """
    Interactive onboarding wizard for new users.
    Probes for company/user info and auto-creates account.
    """

    def __init__(self, llm_manager, config):
        """Initialize onboarding skill"""
        super().__init__(llm_manager, config)
        self.extractor = OnboardingInfoExtractor()
        self.scaffolder = AccountScaffolder()
        self.hierarchy = AccountHierarchy()
        self.claude_loader = ClaudeMdLoader()
        self.logger = logging.getLogger(__name__)
        
        # Onboarding state
        self.state = {
            'stage': 'welcome',  # welcome → company → role → offerings → review → done
            'steps_completed': 0,
            'extracted_info': {}
        }

    async def generate(self, account: Optional[str] = None, **kwargs) -> str:
        """Generate onboarding response"""
        action = kwargs.get('action', 'start')
        user_response = kwargs.get('response', '')
        
        if action == 'start':
            return self._stage_welcome()
        
        elif action == 'next':
            return await self._process_response_and_advance(user_response)
        
        elif action == 'auto_complete':
            # Auto-complete onboarding with extracted info
            return await self._auto_complete_onboarding()
        
        return "Unknown action"

    def _stage_welcome(self) -> str:
        """Welcome stage - introduce JARVIS and start onboarding"""
        self.state['stage'] = 'welcome'
        
        message = """
🎉 **Welcome to JARVIS** - Your Autonomous Sales AI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

I'm JARVIS, your 24/7 AI sales assistant. Over the next few minutes, I'll learn about:
  🏢 Your company and what you sell
  👤 Your role and sales challenges
  📊 Your sales process and goals

Then I'll auto-configure everything and start helping immediately.

**Ready?** Just tell me about your company in a few sentences.

Examples:
  • "I'm at Acme Corp, a 50-person SaaS company in the HR space."
  • "We're a fintech startup offering payment solutions to SMBs."
  • "Our healthcare platform helps hospitals manage patient data."
"""
        self.state['stage'] = 'company'
        return message.strip()

    async def _process_response_and_advance(self, user_response: str) -> str:
        """Process user response and advance to next stage"""
        current_stage = self.state['stage']
        
        if current_stage == 'company':
            return self._stage_company_details(user_response)
        elif current_stage == 'role':
            return self._stage_role(user_response)
        elif current_stage == 'offerings':
            return self._stage_offerings(user_response)
        elif current_stage == 'sales':
            return self._stage_sales_process(user_response)
        elif current_stage == 'review':
            return await self._stage_review(user_response)
        
        return "Onboarding complete!"

    def _stage_company_details(self, response: str) -> str:
        """Extract company details from response"""
        # Analyze the response
        analysis = self.extractor.analyze_response('company', response)
        self.state['extracted_info']['company'] = analysis['extracted']
        self.state['steps_completed'] += 1
        
        # Build confirmation message
        extracted = analysis['extracted']
        parts = []
        
        if extracted.get('name'):
            parts.append(f"✓ Company: **{extracted['name']}**")
        if extracted.get('industry'):
            parts.append(f"✓ Industry: **{extracted['industry']}**")
        if extracted.get('size'):
            parts.append(f"✓ Size: **{extracted['size']}**")
        if extracted.get('revenue'):
            parts.append(f"✓ Revenue: **{extracted['revenue']}**")
        
        confirmation = "\n".join(parts) if parts else "Got it!"
        
        message = f"""{confirmation}

Now, tell me about your role. Are you an AE, presales engineer, sales manager, or something else?
"""
        self.state['stage'] = 'role'
        return message.strip()

    def _stage_role(self, response: str) -> str:
        """Extract user role"""
        analysis = self.extractor.analyze_response('role', response)
        self.state['extracted_info']['user'] = analysis['extracted']
        self.state['steps_completed'] += 1
        
        role = analysis['extracted'].get('role', 'Sales Professional')
        
        message = f"""✓ Role: **{role}**

Perfect! Now, what do you sell? What are your main products or services?
"""
        self.state['stage'] = 'offerings'
        return message.strip()

    def _stage_offerings(self, response: str) -> str:
        """Extract offerings"""
        analysis = self.extractor.analyze_response('offerings', response)
        self.state['extracted_info']['offerings'] = analysis['extracted'].get('offerings', [])
        self.state['steps_completed'] += 1
        
        offerings_str = ", ".join(self.state['extracted_info']['offerings'][:3]) if self.state['extracted_info']['offerings'] else response[:50]
        
        message = f"""✓ Offerings: **{offerings_str}**

Last question: What's your biggest sales challenge right now?
(Examples: long sales cycles, low win rates, slow discovery, proposal turnaround time)
"""
        self.state['stage'] = 'sales'
        return message.strip()

    def _stage_sales_process(self, response: str) -> str:
        """Extract sales process info"""
        analysis = self.extractor.analyze_response('sales', response)
        self.state['extracted_info']['sales'] = analysis['extracted']
        self.state['steps_completed'] += 1
        
        challenges = analysis['extracted'].get('challenges', [])
        challenges_str = ", ".join(challenges) if challenges else "improving efficiency"
        
        message = f"""✓ Focus: **{challenges_str}**

Perfect! Let me review what I learned:

{self._get_summary()}

Ready to create your account? Just confirm and I'll set everything up!
(Type: yes to confirm, or tell me what to change)
"""
        self.state['stage'] = 'review'
        return message.strip()

    async def _stage_review(self, response: str) -> str:
        """Review and confirm before creating account"""
        if response.lower().strip() in ['yes', 'yep', 'confirm', 'go', 'ok', 'okay', 'good']:
            return await self._auto_complete_onboarding()
        else:
            # Allow corrections
            return f"""I'll remember that. Here's the updated info:

{self._get_summary()}

Anything else to change? Or say "yes" to proceed.
"""

    async def _auto_complete_onboarding(self) -> str:
        """Auto-create account and complete onboarding"""
        company_name = self.state['extracted_info'].get('company', {}).get('name')
        
        if not company_name:
            return "I need a company name to create your account. Please tell me your company name."
        
        try:
            # Prepare company info for scaffolding
            company_info = {
                'company_name': company_name,
                'industry': self.state['extracted_info'].get('company', {}).get('industry', 'Technology'),
                'revenue': self.state['extracted_info'].get('company', {}).get('revenue', 'Unknown'),
                'employees': self._estimate_employees(self.state['extracted_info'].get('company', {}).get('size')),
                'offerings': ', '.join(self.state['extracted_info'].get('offerings', [])),
                'user_role': self.state['extracted_info'].get('user', {}).get('role', 'Sales Professional'),
            }
            
            # Create account
            self.logger.info(f"Auto-scaffolding account for {company_name}")
            result = self.scaffolder.scaffold_account(company_name, company_info)
            
            if result['status'] != 'created':
                return f"Account already exists! Using {company_name}."
            
            # Load config for new account
            account_path = self.hierarchy.get_account_path(company_name)
            if account_path:
                self.claude_loader.load_config(str(account_path), force_reload=True)
            
            # Generate welcome message
            return f"""
✅ **Account Created!** 

📁 **{company_name}** is ready to go!

**Created files:**
  ✓ company_research.md - Your company overview
  ✓ discovery.md - Sales discovery template
  ✓ deal_stage.json - Deal pipeline tracker
  ✓ CLAUDE.md - Your account configuration

**What's Next?**

1️⃣ **Upload files** - Drop proposals, contracts, or competitor docs in cowork
2️⃣ **Start selling** - Use skills like:
   • /get_proposal - Generate proposals
   • /get_battlecard - Create competitor battlecards
   • /get_discovery - Plan discovery calls
   • /get_demo_strategy - Plan demos

3️⃣ **Keep improving** - I learn from every file and conversation

I'm learning about {company_name} now. Drop files in cowork and I'll analyze them!

**Your next move?** Upload a recent proposal or competitor analysis.
"""
        
        except Exception as e:
            self.logger.error(f"Failed to complete onboarding: {e}")
            return f"Error creating account: {str(e)}"

    def _get_summary(self) -> str:
        """Get summary of extracted information"""
        lines = []
        
        company = self.state['extracted_info'].get('company', {})
        if company.get('name'):
            summary_parts = [company['name']]
            if company.get('industry'):
                summary_parts.append(f"{company['industry']}")
            if company.get('size'):
                summary_parts.append(f"({company['size']})")
            lines.append(f"📍 **Company**: {' '.join(summary_parts)}")
        
        user = self.state['extracted_info'].get('user', {})
        if user.get('role'):
            lines.append(f"👤 **Your Role**: {user['role']}")
        
        offerings = self.state['extracted_info'].get('offerings', [])
        if offerings:
            lines.append(f"📦 **You Sell**: {', '.join(offerings[:2])}")
        
        sales = self.state['extracted_info'].get('sales', {})
        if sales.get('challenges'):
            lines.append(f"🎯 **Focus Area**: {', '.join(sales['challenges'][:2])}")
        
        return "\n".join(lines) if lines else "Company profile gathering..."

    def _estimate_employees(self, size_str: Optional[str]) -> str:
        """Estimate employee count from size string"""
        size_map = {
            'startup': '1-10',
            'small': '11-50',
            'mid-market': '51-500',
            'enterprise': '500+',
        }
        return size_map.get(size_str, 'Unknown')

    async def generate_summary(self) -> str:
        """Get skill summary"""
        return """
OnboardingSkill: Interactive setup wizard for JARVIS
- Intelligently probes for company information
- Extracts details from natural language responses
- Auto-creates account with pre-filled templates
- Guides new users to first successful skill usage
"""
