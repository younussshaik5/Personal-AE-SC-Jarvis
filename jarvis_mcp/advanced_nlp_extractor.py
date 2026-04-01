"""
AdvancedNLPExtractor - Enhanced NLP for extracting information from unstructured text.
Uses: pattern matching, context analysis, entity recognition, semantic understanding.
"""

import re
from typing import Dict, List, Any, Optional, Set
import logging


class AdvancedNLPExtractor:
    """
    Advanced natural language processing for sales intelligence extraction.
    Goes beyond regex - understands context and semantic meaning.
    """

    def __init__(self):
        """Initialize extractor"""
        self.logger = logging.getLogger(__name__)
        
        # Semantic maps for better understanding
        self.challenge_synonyms = {
            'discovery': ['discovery', 'qualification', 'discovery phase', 'discovery call', 'needs analysis', 'requirement gathering'],
            'cycle_time': ['sales cycle', 'cycle time', 'deal closing', 'long cycle', 'lengthy process', 'time to close'],
            'win_rate': ['win rate', 'close rate', 'conversion', 'closing ratio', 'deal wins', 'success rate'],
            'proposal': ['proposal', 'rfp response', 'rfi', 'response', 'documentation', 'proposal writing'],
            'pricing': ['pricing', 'negotiation', 'discount', 'margin', 'price', 'cost'],
            'competition': ['competition', 'competitors', 'competitive', 'losing deals', 'deal slippage'],
        }
        
        self.company_size_patterns = {
            'startup': [
                r'\bstartup\b', r'early stage', r'seed funded', r'series [a-z]',
                r'<\s*10\s+(?:people|employees|person)', r'bootstrapped'
            ],
            'small': [
                r'\b(?:small|sme|smb)\b', r'10\s*[-–]\s*50', r'10-100',
                r'50\s+(?:people|employees)'
            ],
            'mid-market': [
                r'mid.?market', r'mid.?size', r'100\s*[-–]\s*500', r'500\s*[-–]\s*1000',
                r'growing (?:company|business)'
            ],
            'enterprise': [
                r'\benterprise\b', r'\blarge\b', r'\bfortune\b', r'>500', r'1000\+',
                r'global (?:company|corporation)', r'multinational'
            ],
        }

    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        Extract all information from text comprehensively.
        
        Returns:
            Dict with extracted: company, industry, size, revenue, challenges, etc.
        """
        results = {
            'company': self.extract_company(text),
            'industry': self.extract_industry(text),
            'size': self.extract_size(text),
            'revenue': self.extract_revenue(text),
            'role': self.extract_role(text),
            'offerings': self.extract_offerings(text),
            'challenges': self.extract_challenges(text),
            'customer_base': self.extract_customer_base(text),
            'decision_makers': self.extract_decision_makers(text),
        }
        return {k: v for k, v in results.items() if v}

    def extract_company(self, text: str) -> Optional[str]:
        """Extract company name with context awareness"""
        # Look for company name patterns with context
        patterns = [
            r'(?:at|from|work(?:ing)?(?:\s+)?at|company|organization)\s+([A-Z][a-zA-Z0-9\s&]+?)(?:\s*(?:is|operates|does|sells|provides),|[\.,]|$)',
            r'([A-Z][a-zA-Z0-9\s&]+?)\s+(?:is|operates|does|sells|focuses|specializes)',
            r'(?:we|our)\s+(?:company|organization|firm)(?:\s+is)?\s*:?\s*([A-Z][a-zA-Z0-9\s&]+?)(?:,|\.)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                if 3 < len(company) < 100 and not company.lower().startswith(('the ', 'we ', 'our ')):
                    return company
        
        return None

    def extract_industry(self, text: str) -> Optional[str]:
        """Extract industry with semantic understanding"""
        industry_map = {
            'SaaS': r'\b(?:saas|software|cloud|platform|application|web (?:application|app))\b',
            'Finance': r'\b(?:fintech|banking|financial|insurance|payments|paytech)\b',
            'Healthcare': r'\b(?:healthcare|health tech|medical|pharma|biotech|hospital|clinic)\b',
            'E-commerce': r'\b(?:ecommerce|e-commerce|retail|online|marketplace|shopping)\b',
            'Manufacturing': r'\b(?:manufacturing|industrial|supply chain|factory|production)\b',
            'Telecom': r'\b(?:telecom|telecommunications|mobile|network|connectivity|carrier)\b',
            'Media': r'\b(?:media|publishing|content|news|broadcast)\b',
            'Technology': r'\b(?:technology|tech|it services|software|consulting)\b',
            'Education': r'\b(?:education|edtech|learning|training|university|school)\b',
            'Travel': r'\b(?:travel|hospitality|tourism|hotel|airline|booking)\b',
            'Logistics': r'\b(?:logistics|shipping|transport|delivery|freight)\b',
        }
        
        text_lower = text.lower()
        for industry, pattern in industry_map.items():
            if re.search(pattern, text_lower):
                return industry
        
        return None

    def extract_size(self, text: str) -> Optional[str]:
        """Extract company size with pattern matching"""
        text_lower = text.lower()
        
        for size, patterns in self.company_size_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return size
        
        return None

    def extract_revenue(self, text: str) -> Optional[str]:
        """Extract revenue with format understanding"""
        patterns = [
            (r'\$(\d+)\s*[mb]', lambda m: f"${m.group(1)}M"),
            (r'(\d+)\s*(?:million|m)\b', lambda m: f"${m.group(1)}M"),
            (r'\$(\d+)\s*[bg]', lambda m: f"${m.group(1)}B"),
            (r'(\d+)\s*(?:billion|b)\b', lambda m: f"${m.group(1)}B"),
            (r'\$(\d+)\s*[kg]', lambda m: f"${m.group(1)}K"),
            (r'(\d+)\s*(?:thousand|k)\b', lambda m: f"${m.group(1)}K"),
        ]
        
        for pattern, formatter in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return formatter(match)
        
        return None

    def extract_role(self, text: str) -> Optional[str]:
        """Extract user role with semantic matching"""
        roles = {
            'Sales Executive': [r'\b(?:ae|account executive|account manager|sales rep|sales executive)\b'],
            'Sales Manager': [r'\b(?:sales manager|sales director|vp sales|vp of sales|head of sales)\b'],
            'Presales': [r'\b(?:presales|pre-sales|sa|solution architect|sales engineer|solutions engineer)\b'],
            'Marketing': [r'\b(?:marketing|product marketing|demand gen|growth marketing)\b'],
            'Revenue': [r'\b(?:revenue ops|go-to-market|gtm)\b'],
            'Founder': [r'\b(?:founder|ceo|cto|cfo|executive|owner)\b'],
        }
        
        text_lower = text.lower()
        for role, patterns in roles.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return role
        
        return None

    def extract_offerings(self, text: str) -> List[str]:
        """Extract products/services"""
        offerings = []
        
        patterns = [
            r'we (?:sell|offer|provide|build)\s+([a-z\s,&and]+?)(?:to|for|that|which)',
            r'our (?:product|solution|service|offering)(?:s)?\s+(?:is|are|includes?)\s+([a-z\s,&and]+?)(?:,|\.)',
            r'we (?:help|enable)\s+(?:companies|customers)\s+(?:with|to|manage)\s+([a-z\s,&and]+?)(?:,|\.)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                offering = match.strip().strip(',').strip('and').strip()
                if 3 < len(offering) < 100:
                    offerings.append(offering)
        
        return list(set(offerings))  # Remove duplicates

    def extract_challenges(self, text: str) -> List[str]:
        """Extract sales challenges with semantic understanding"""
        challenges = []
        text_lower = text.lower()
        
        for challenge, keywords in self.challenge_synonyms.items():
            for keyword in keywords:
                if re.search(rf'\b{re.escape(keyword)}\b', text_lower):
                    challenges.append(challenge)
                    break
        
        return challenges

    def extract_customer_base(self, text: str) -> Optional[str]:
        """Extract target customer base"""
        patterns = [
            r'(?:target|serve|sell to|work with)\s+([a-z\s]+?)(?:companies?|customers?|market)',
            r'(?:enterprise|smb|mid-market|startup)s?\s+(?:in|across)\s+([a-z\s]+?)(?:industry|market)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None

    def extract_decision_makers(self, text: str) -> List[str]:
        """Extract roles of decision makers mentioned"""
        decision_makers = []
        
        titles = ['CEO', 'CTO', 'CFO', 'COO', 'VP', 'Director', 'Manager', 'Head', 'C-level', 'Executive']
        
        for title in titles:
            if re.search(rf'\b{title}\b', text, re.IGNORECASE):
                decision_makers.append(title)
        
        return decision_makers

    def extract_sentiment(self, text: str) -> str:
        """Extract sentiment about challenges/products"""
        positive = len(re.findall(r'\b(?:great|excellent|amazing|love|best|preferred|leading)\b', text, re.IGNORECASE))
        negative = len(re.findall(r'\b(?:problem|challenge|difficult|struggling|issue|bad|worst)\b', text, re.IGNORECASE))
        
        if positive > negative:
            return 'positive'
        elif negative > positive:
            return 'negative'
        else:
            return 'neutral'
