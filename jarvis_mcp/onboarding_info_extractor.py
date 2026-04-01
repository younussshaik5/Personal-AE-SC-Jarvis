"""
OnboardingInfoExtractor - Intelligently extracts company and user info from natural language.
Parses responses to onboarding questions and structures them for account creation.
"""

import re
from typing import Dict, Any, Optional, List
import logging


class OnboardingInfoExtractor:
    """
    Extracts structured information from conversational responses.
    Learns from user's natural language to populate account details.
    """

    def __init__(self):
        """Initialize extractor"""
        self.logger = logging.getLogger(__name__)
        self.extracted_info = {
            'user': {},
            'company': {},
            'sales': {},
            'offerings': []
        }

    def extract_company_name(self, text: str) -> Optional[str]:
        """Extract company name from text"""
        # Look for common patterns:
        # "At [Company]", "company [Company]", "working on [Company]", "[Company] is our company"
        patterns = [
            r"(?:at|from|work(?:ing)?(?:\s+)?at|company\s+(?:is\s+)?)?([A-Z][a-zA-Z\s&]+?)(?:\s+(?:is|operates|does|sells|provides)|,|\.)",
            r"([A-Z][a-zA-Z\s&]+?)\s+(?:is|operates|does|sells|focuses|specializes)",
            r"(?:we|our)\s+(?:company|organization|firm)(?:\s+is)?:?\s+([A-Z][a-zA-Z\s&]+?)(?:,|\.)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if len(company) > 2 and len(company) < 100:
                    self.extracted_info['company']['name'] = company
                    self.logger.info(f"Extracted company name: {company}")
                    return company
        
        return None

    def extract_industry(self, text: str) -> Optional[str]:
        """Extract industry from text"""
        industries = {
            'SaaS': ['saas', 'software', 'cloud', 'platform', 'application'],
            'Finance': ['fintech', 'banking', 'financial', 'insurance', 'payments'],
            'Healthcare': ['healthcare', 'health tech', 'medical', 'pharma', 'biotech'],
            'E-commerce': ['ecommerce', 'retail', 'online store', 'marketplace'],
            'Manufacturing': ['manufacturing', 'industrial', 'supply chain'],
            'Telecom': ['telecom', 'telecommunications', 'mobile', 'network'],
            'Media': ['media', 'publishing', 'content', 'news'],
            'Technology': ['tech', 'technology', 'it services', 'consulting'],
            'Education': ['education', 'edtech', 'learning', 'training'],
            'Travel': ['travel', 'hospitality', 'tourism', 'hotel'],
        }
        
        text_lower = text.lower()
        for industry, keywords in industries.items():
            for keyword in keywords:
                if keyword in text_lower:
                    self.extracted_info['company']['industry'] = industry
                    self.logger.info(f"Detected industry: {industry}")
                    return industry
        
        return None

    def extract_company_size(self, text: str) -> Optional[str]:
        """Extract company size/employee count"""
        size_patterns = {
            'startup': [r'\bstartup\b', r'<10\s+(?:people|employees)', r'early stage'],
            'small': [r'\b(small|sme)\b', r'10-50\s+(?:people|employees)', r'20-100'],
            'mid-market': [r'mid.?market', r'mid.?size', r'100-500\s+(?:people|employees)', r'growing'],
            'enterprise': [r'enterprise', r'large', r'>500\s+employees', r'\d{4}\+\s+employees'],
        }
        
        text_lower = text.lower()
        for size, patterns in size_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    self.extracted_info['company']['size'] = size
                    self.logger.info(f"Detected company size: {size}")
                    return size
        
        return None

    def extract_revenue(self, text: str) -> Optional[str]:
        """Extract revenue information"""
        patterns = [
            (r'\$(\d+)M', lambda m: f"${m.group(1)}M"),
            (r'(\d+)\s+million', lambda m: f"${m.group(1)}M"),
            (r'\$(\d+)B', lambda m: f"${m.group(1)}B"),
            (r'(\d+)\s+billion', lambda m: f"${m.group(1)}B"),
            (r'\$(\d+)K', lambda m: f"${m.group(1)}K"),
            (r'(\d+)\s+thousand', lambda m: f"${m.group(1)}K"),
        ]
        
        for pattern, formatter in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                revenue = formatter(match)
                self.extracted_info['company']['revenue'] = revenue
                self.logger.info(f"Extracted revenue: {revenue}")
                return revenue
        
        return None

    def extract_user_role(self, text: str) -> Optional[str]:
        """Extract user's role/title"""
        roles = {
            'Sales Executive': ['sales executive', 'account executive', 'ae', 'sales rep'],
            'Sales Manager': ['sales manager', 'sales director', 'vp sales', 'head of sales'],
            'Presales': ['presales', 'pre-sales', 'sa', 'solution architect', 'sales engineer'],
            'Marketing': ['marketing', 'product marketing', 'demand gen'],
            'Revenue': ['revenue ops', 'go-to-market', 'growth'],
            'Founder': ['founder', 'ceo', 'cto', 'cfo', 'executive'],
        }
        
        text_lower = text.lower()
        for role, keywords in roles.items():
            for keyword in keywords:
                if keyword in text_lower:
                    self.extracted_info['user']['role'] = role
                    self.logger.info(f"Detected user role: {role}")
                    return role
        
        return None

    def extract_offerings(self, text: str) -> List[str]:
        """Extract product/service offerings"""
        offerings = []
        
        # Common offering patterns
        patterns = [
            r"we (?:sell|offer|provide|build)\s+([a-z\s,&and]+?)(?:to|for|that)",
            r"our (?:product|solution|service|offering)(?:s)?\s+(?:is|are|include)s?\s+([a-z\s,&and]+?)(?:,|\.)",
            r"we (?:help|enable)\s+(?:companies|customers)\s+(?:with|to|manage)\s+([a-z\s,&and]+?)(?:,|\.)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean up the offering
                offering = match.strip().strip(',').strip('and').strip()
                if len(offering) > 3 and len(offering) < 100:
                    offerings.append(offering)
        
        if offerings:
            self.extracted_info['offerings'] = offerings
            self.logger.info(f"Extracted offerings: {offerings}")
        
        return offerings

    def extract_sales_process(self, text: str) -> Optional[str]:
        """Infer sales process from text"""
        processes = {
            'land-and-expand': ['land and expand', 'upsell', 'cross-sell', 'existing customers'],
            'enterprise-deal': ['enterprise', 'complex deals', 'long sales cycle', 'procurement'],
            'transactional': ['quick', 'self-serve', 'low friction', 'instant'],
            'consultative': ['consultative', 'advisory', 'strategic', 'partnership'],
        }
        
        text_lower = text.lower()
        for process, keywords in processes.items():
            for keyword in keywords:
                if keyword in text_lower:
                    self.extracted_info['sales']['process'] = process
                    self.logger.info(f"Detected sales process: {process}")
                    return process
        
        return None

    def extract_challenges(self, text: str) -> List[str]:
        """Extract sales challenges mentioned"""
        challenges = []
        
        # Challenge keywords
        keywords = {
            'long sales cycles': ['long sales cycle', 'slow', 'time to close'],
            'deal velocity': ['deal velocity', 'pipeline', 'throughput'],
            'win rates': ['win rate', 'lost deals', 'competitive'],
            'discovery': ['discovery', 'qualification', 'understanding needs'],
            'proposal writing': ['proposal', 'rfi', 'response'],
            'customer retention': ['churn', 'retention', 'upsell'],
        }
        
        text_lower = text.lower()
        for challenge, keywords_list in keywords.items():
            for keyword in keywords_list:
                if keyword in text_lower:
                    challenges.append(challenge)
                    break
        
        if challenges:
            self.extracted_info['sales']['challenges'] = challenges
            self.logger.info(f"Detected challenges: {challenges}")
        
        return challenges

    def get_extracted_info(self) -> Dict[str, Any]:
        """Get all extracted information"""
        return self.extracted_info

    def get_summary(self) -> str:
        """Get human-readable summary of extracted info"""
        lines = []
        
        if self.extracted_info['company'].get('name'):
            lines.append(f"Company: {self.extracted_info['company']['name']}")
        if self.extracted_info['company'].get('industry'):
            lines.append(f"Industry: {self.extracted_info['company']['industry']}")
        if self.extracted_info['company'].get('size'):
            lines.append(f"Size: {self.extracted_info['company']['size']}")
        if self.extracted_info['company'].get('revenue'):
            lines.append(f"Revenue: {self.extracted_info['company']['revenue']}")
        if self.extracted_info['user'].get('role'):
            lines.append(f"Your role: {self.extracted_info['user']['role']}")
        if self.extracted_info['offerings']:
            lines.append(f"Offerings: {', '.join(self.extracted_info['offerings'][:3])}")
        if self.extracted_info['sales'].get('challenges'):
            lines.append(f"Key challenges: {', '.join(self.extracted_info['sales']['challenges'][:2])}")
        
        return "\n".join(lines) if lines else "No information extracted yet"

    def analyze_response(self, question_type: str, response: str) -> Dict[str, Any]:
        """Analyze a response to a specific question"""
        analysis = {'question_type': question_type, 'extracted': {}}
        
        if question_type == 'company':
            analysis['extracted']['name'] = self.extract_company_name(response)
            analysis['extracted']['industry'] = self.extract_industry(response)
            analysis['extracted']['size'] = self.extract_company_size(response)
            analysis['extracted']['revenue'] = self.extract_revenue(response)
        
        elif question_type == 'role':
            analysis['extracted']['role'] = self.extract_user_role(response)
        
        elif question_type == 'offerings':
            analysis['extracted']['offerings'] = self.extract_offerings(response)
        
        elif question_type == 'sales':
            analysis['extracted']['process'] = self.extract_sales_process(response)
            analysis['extracted']['challenges'] = self.extract_challenges(response)
        
        return analysis
