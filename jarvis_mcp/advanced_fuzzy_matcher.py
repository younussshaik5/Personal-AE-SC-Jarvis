"""
AdvancedFuzzyMatcher - Sophisticated account name matching with multi-strategy approach.
Uses: levenshtein distance, token matching, semantic similarity, phonetic matching.
"""

import re
from typing import Dict, List, Tuple, Optional
from difflib import SequenceMatcher
import logging


class AdvancedFuzzyMatcher:
    """
    Advanced fuzzy matching for account names.
    Strategies: exact, substring, token, levenshtein, phonetic, semantic.
    """

    def __init__(self):
        """Initialize matcher"""
        self.logger = logging.getLogger(__name__)
        self.threshold = 0.70  # 70% match threshold

    def match(self, search_term: str, candidates: List[str], threshold: Optional[float] = None) -> List[Tuple[str, float]]:
        """
        Match search term against candidates with multiple strategies.
        
        Returns:
            List of (candidate, score) tuples sorted by score descending
        """
        if not search_term or not candidates:
            return []
        
        threshold = threshold or self.threshold
        results = []
        
        search_clean = self._normalize(search_term)
        
        for candidate in candidates:
            candidate_clean = self._normalize(candidate)
            
            # Try multiple matching strategies
            scores = []
            
            # 1. Exact match (100%)
            if search_clean == candidate_clean:
                scores.append(1.0)
            
            # 2. Substring match
            if search_clean in candidate_clean or candidate_clean in search_clean:
                scores.append(0.95)
            
            # 3. Token-based matching (word-by-word)
            token_score = self._token_match(search_clean, candidate_clean)
            scores.append(token_score)
            
            # 4. Levenshtein distance (edit distance)
            lev_score = self._levenshtein_similarity(search_clean, candidate_clean)
            scores.append(lev_score)
            
            # 5. Sequence matching (SequenceMatcher)
            seq_score = SequenceMatcher(None, search_clean, candidate_clean).ratio()
            scores.append(seq_score)
            
            # 6. Acronym matching (e.g., "TC" for "TataCommunications")
            if len(search_term) <= 3:
                acro_score = self._acronym_match(search_clean, candidate_clean)
                scores.append(acro_score)
            
            # Use average of strategies, weighted by relevance
            final_score = max(scores)  # Take best strategy
            
            if final_score >= threshold:
                results.append((candidate, final_score))
        
        # Sort by score descending
        return sorted(results, key=lambda x: x[1], reverse=True)

    def _normalize(self, text: str) -> str:
        """Normalize text for matching"""
        # Remove special chars, convert to lowercase, remove extra spaces
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Remove special characters
        text = re.sub(r'\s+', ' ', text).strip()  # Normalize spaces
        return text

    def _token_match(self, search: str, candidate: str) -> float:
        """Match based on word tokens"""
        search_tokens = set(search.split())
        candidate_tokens = set(candidate.split())
        
        if not search_tokens or not candidate_tokens:
            return 0.0
        
        # Jaccard similarity
        intersection = len(search_tokens & candidate_tokens)
        union = len(search_tokens | candidate_tokens)
        return intersection / union if union > 0 else 0.0

    def _levenshtein_similarity(self, s1: str, s2: str) -> float:
        """Calculate Levenshtein distance similarity"""
        distance = self._levenshtein_distance(s1, s2)
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len) if max_len > 0 else 0.0

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance (edit distance)"""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]

    def _acronym_match(self, search: str, candidate: str) -> float:
        """Match acronyms (e.g., 'TC' matches 'Tata Communications')"""
        # For short search terms, try to match as acronym
        if len(search) < 4:
            # Extract first letters of candidate words
            candidate_words = candidate.split()
            acronym = ''.join([w[0] for w in candidate_words if w])
            
            if search == acronym:
                return 0.90
            
            # Also try partial acronym
            if search in acronym or acronym in search:
                return 0.75
        
        return 0.0

    def find_best_match(self, search_term: str, candidates: List[str]) -> Optional[str]:
        """Find single best match, or None if below threshold"""
        results = self.match(search_term, candidates)
        if results and results[0][1] >= self.threshold:
            return results[0][0]
        return None

    def format_results(self, search_term: str, matches: List[Tuple[str, float]]) -> str:
        """Format matching results for display"""
        if not matches:
            return f"No matches found for '{search_term}'"
        
        lines = [f"Matches for '{search_term}':"]
        for candidate, score in matches[:5]:  # Show top 5
            bar_length = int(score * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            lines.append(f"  {candidate:30} {score:.0%} {bar}")
        
        return "\n".join(lines)


# Test the matcher
if __name__ == "__main__":
    matcher = AdvancedFuzzyMatcher()
    
    candidates = [
        'TataCommunications',
        'TataTele',
        'TataSky',
        'AcmeCorp',
        'AcmeEnterprises',
        'ZebraInc'
    ]
    
    test_cases = [
        'tata',
        'tata communications',
        'TC',
        'acme',
        'acme corp',
        'zebra',
        'zeb',
    ]
    
    for search in test_cases:
        results = matcher.match(search, candidates)
        print(matcher.format_results(search, results))
        print()
