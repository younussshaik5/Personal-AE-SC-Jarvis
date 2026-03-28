#!/usr/bin/env python3
"""Dynamic Research Service - Real-time data fetching for all skills."""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional
from jarvis.utils.logger import JARVISLogger
from jarvis.llm.llm_client import LLMManager
from jarvis.utils.config import ConfigManager


class DynamicResearchService:
    """Provides real-time research capabilities for all skills."""
    
    def __init__(self, config_manager: ConfigManager, llm: Optional[LLMManager] = None):
        self.config = config_manager.config
        self.llm = llm
        self.logger = JARVISLogger("research_service")
        self.session: Optional[aiohttp.ClientSession] = None
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes
        
    async def start(self):
        """Initialize HTTP session."""
        self.session = aiohttp.ClientSession()
        
    async def stop(self):
        """Cleanup."""
        if self.session:
            await self.session.close()
    
    # ========== COMPANY RESEARCH ==========
    async def research_company(self, company: str) -> Dict[str, Any]:
        """Comprehensive company research including K10 financial metrics."""
        cache_key = f"company:{company.lower()}"
        if cached := self._get_cached(cache_key):
            return cached
            
        results = {
            "company": company,
            "financials": {},
            "k10_metrics": {},  # Key financial metrics
            "leadership": [],
            "news": [],
            "tech_stack": {},
            "industry": "",
            "priorities": []
        }
        
        if not self.session:
            return results
            
        # Search K10 financial reports (10-K, earnings, revenue, growth)
        try:
            k10_data = await self._web_search(f"{company} 10-K annual report {2024} revenue cogs opex")
            results["k10_metrics"] = self._extract_k10_metrics(k10_data)
        except Exception as e:
            self.logger.debug("K10 extraction failed", company=company, error=str(e))
            
        # Also get recent earnings call transcripts for priorities
        try:
            earnings = await self._web_search(f"{company} earnings Q4 2024 Q1 2025 transcript priorities")
            if not results["k10_metrics"]:
                results["financials"] = self._extract_financials_from_earnings(earnings)
            results["priorities"] = self._extract_earnings_priorities(earnings)
        except:
            pass
            
        # Search leadership
        try:
            leadership = await self._web_search(f"{company} CIO CTO VP Customer Service leadership")
            results["leadership"] = self._extract_leadership(leadership)
        except:
            pass
            
        # Search tech stack
        try:
            tech = await self._web_search(f"{company} customer service platform CRM tools")
            results["tech_stack"] = self._infer_tech_stack(tech)
        except:
            pass
            
        # Search industry trends if not already set
        if not results["industry"]:
            try:
                trends = await self._web_search(f"{company} industry challenges 2025")
                results["industry"] = self._extract_industry(trends)
                if not results["priorities"]:
                    results["priorities"] = self._extract_priorities(trends)
            except:
                pass
            
        self._cache(cache_key, results)
        return results
    
    # ========== EXECUTIVE RESEARCH ==========
    async def research_executive(self, name: str, company: str) -> Dict[str, Any]:
        """Research specific executive using LinkedIn, news, earnings calls."""
        cache_key = f"exec:{name.lower()}:{company.lower()}"
        if cached := self._get_cached(cache_key):
            return cached
            
        result = {
            "name": name,
            "company": company,
            "title": "",
            "background": [],
            "priorities": [],
            "recent_mentions": []
        }
        
        try:
            # Search LinkedIn profile insights (via web)
            linkedin = await self._web_search(f"{name} {company} LinkedIn")
            result.update(self._parse_linkedin(linkedin))
        except:
            pass
            
        try:
            # Search recent speeches, interviews
            speeches = await self._web_search(f"{name} interview talk 2024 2025")
            result["recent_mentions"] = self._extract_mentions(speeches)
        except:
            pass
            
        try:
            # Search for priorities in earnings calls
            priorities = await self._web_search(f"{company} earnings {name} priorities")
            result["priorities"] = self._extract_priorities(priorities)
        except:
            pass
            
        self._cache(cache_key, result)
        return result
    
    # ========== COMPETITIVE INTELLIGENCE ==========
    async def research_competitor(self, competitor: str, product: str = "") -> Dict[str, Any]:
        """Real-time competitive intelligence: pricing, features, sentiment."""
        cache_key = f"comp:{competitor.lower()}"
        if cached := self._get_cached(cache_key):
            return cached
            
        result = {
            "competitor": competitor,
            "pricing": {},
            "features": [],
            "g2_sentiment": {},
            "recent_news": [],
            "weaknesses": []
        }
        
        try:
            # Pricing search
            pricing = await self._web_search(f"{competitor} pricing {2024} 2025")
            result["pricing"] = self._extract_pricing(pricing, competitor)
        except:
            pass
            
        try:
            # G2 reviews (via web search)
            g2 = await self._web_search(f"{competitor} G2 reviews pros cons")
            result["g2_sentiment"] = self._parse_g2(g2)
        except:
            pass
            
        try:
            # Recent product updates
            updates = await self._web_search(f"{competitor} new features 2024 2025")
            result["features"] = self._extract_feature_updates(updates)
        except:
            pass
            
        try:
            # Competitive weaknesses from reviews
            company_name = self.config.get("identity", {}).get("company", "Your Company")
            weaknesses = await self._web_search(f"{competitor} vs {company_name} disadvantages")
            result["weaknesses"] = self._extract_weaknesses(weaknesses)
        except:
            pass
            
        self._cache(cache_key, result)
        return result
    
    # ========== PRICING INTELLIGENCE ==========
    async def get_competitor_pricing(self, tool_name: str) -> Dict[str, Any]:
        """Fetch current pricing for a competitor tool."""
        cache_key = f"price:{tool_name.lower()}"
        if cached := self._get_cached(cache_key):
            return cached
            
        try:
            search_results = await self._web_search(f"{tool_name} pricing per agent per month 2025")
            pricing = self._parse_pricing(search_results, tool_name)
            self._cache(cache_key, pricing)
            return pricing
        except:
            # Fallback to known baseline
            return {"tool": tool_name, "price": None, "source": "failed", "confidence": "low"}
    
    # ========== INDUSTRY BENCHMARKS ==========
    async def get_industry_benchmarks(self, industry: str, metric: str = "") -> Dict[str, Any]:
        """Get industry-specific benchmarks and averages."""
        cache_key = f"industry:{industry.lower()}:{metric}"
        if cached := self._get_cached(cache_key):
            return cached
            
        try:
            query = f"{industry} {metric} benchmark 2025" if metric else f"{industry} benchmarks 2025"
            results = await self._web_search(query)
            benchmarks = self._extract_benchmarks(results, industry, metric)
            self._cache(cache_key, benchmarks)
            return benchmarks
        except:
            return {}
    
    # ========== COMPANY PRODUCT KNOWLEDGE ==========
    async def get_company_capabilities(self, product: str, feature: str = "") -> Dict[str, Any]:
        """Get current company product capabilities and pricing."""
        cache_key = f"fw:{product.lower()}:{feature}"
        if cached := self._get_cached(cache_key):
            return cached

        company_name = self.config.get("identity", {}).get("company", "Your Company")
        try:
            # Search company official docs/pricing
            query = f"{company_name} {product} {feature} pricing features 2025" if feature else f"{company_name} {product} pricing features 2025"
            results = await self._web_search(query)
            capabilities = self._extract_fw_capabilities(results, product, feature)
            self._cache(cache_key, capabilities)
            return capabilities
        except:
            return {}
    
    # ========== RISK SIGNALS ==========
    async def check_company_risks(self, company: str) -> List[Dict[str, Any]]:
        """Check for risk signals: layoffs, budget freezes, mergers."""
        cache_key = f"risk:{company.lower()}"
        if cached := self._get_cached(cache_key):
            return cached
            
        risks = []
        risk_queries = [
            f"{company} layoff 2024 2025",
            f"{company} budget freeze",
            f"{company} merger acquisition",
            f"{company} CIO change 2024 2025"
        ]
        
        for query in risk_queries:
            try:
                results = await self._web_search(query)
                if self._contains_risk_signal(results, query):
                    risks.append({
                        "type": self._classify_risk(query),
                        "signal": query,
                        "source": "web_search",
                        "timestamp": "now"
                    })
            except:
                pass
                
        self._cache(cache_key, risks)
        return risks
    
    # ========== HELPER METHODS ==========
    async def _web_search(self, query: str) -> List[str]:
        """Execute web search using DuckDuckGo with proper headers and error handling."""
        if not self.session:
            return []
        
        try:
            from urllib.parse import quote_plus
            import re
            
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (JARVIS Research Bot; OpenCode) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://duckduckgo.com/'
            }
            
            async with self.session.get(url, headers=headers, timeout=15) as resp:
                if resp.status != 200:
                    self.logger.warning("Web search failed", query=query, status=resp.status)
                    return []
                
                html = await resp.text()
            
            # Parse results
            results = []
            link_pattern = re.compile(r'<a class="result__a" href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
            snippet_pattern = re.compile(r'<a class="result__snippet">(.*?)</a>', re.DOTALL)
            
            links = link_pattern.findall(html)
            snippets = snippet_pattern.findall(html)
            
            # Pair them and create text snippets
            for i, (href, title_html) in enumerate(links[:5]):  # top 5
                title = re.sub(r'<[^>]+>', '', title_html).strip()
                snippet = ''
                if i < len(snippets):
                    snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                
                # Combine into a search result text
                result_text = f"{title}\n{snippet}" if snippet else title
                results.append(result_text)
            
            # Cache successful results for future reuse
            self._cache(cache_key, results)
            return results
        
        except Exception as e:
            self.logger.warning("Web search error", query=query, error=str(e))
            return []
            
        try:
            from urllib.parse import quote_plus
            import re
            
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (JARVIS Research Bot) AppleWebKit/537.36'
            }
            
            async with self.session.get(url, headers=headers, timeout=10) as resp:
                if resp.status != 200:
                    self.logger.warning("Web search failed", query=query, status=resp.status)
                    return []
                
                html = await resp.text()
                
            # Parse results
            results = []
            link_pattern = re.compile(r'<a class="result__a" href="([^"]+)".*?>(.*?)</a>', re.DOTALL)
            snippet_pattern = re.compile(r'<a class="result__snippet">(.*?)</a>', re.DOTALL)
            
            links = link_pattern.findall(html)
            snippets = snippet_pattern.findall(html)
            
            # Pair them and create text snippets
            for i, (href, title_html) in enumerate(links[:5]):  # top 5
                title = re.sub(r'<[^>]+>', '', title_html).strip()
                snippet = ''
                if i < len(snippets):
                    snippet = re.sub(r'<[^>]+>', '', snippets[i]).strip()
                
                # Combine into a search result text
                result_text = f"{title}\n{snippet}" if snippet else title
                results.append(result_text)
            
            return results
            
        except Exception as e:
            self.logger.warning("Web search error", query=query, error=str(e))
            return []
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get from cache if fresh."""
        entry = self.cache.get(key)
        if entry:
            import time
            if time.time() - entry.get("_ts", 0) < self.cache_ttl:
                return entry.get("data")
        return None
    
    def _cache(self, key: str, data: Any):
        """Cache with timestamp."""
        import time
        self.cache[key] = {"data": data, "_ts": time.time()}
    
    # Extraction methods (to be implemented with regex/NLP/LLM)
    def _extract_financials(self, text: str) -> Dict[str, Any]:
        """Extract revenue, growth from search snippets."""
        # Use LLM to parse
        return {"raw": text[:200]}
    
    def _extract_leadership(self, text: str) -> List[Dict[str, str]]:
        """Extract executive names and titles."""
        return []
    
    def _infer_tech_stack(self, text: str) -> Dict[str, str]:
        """Infer current tools from job postings, reviews."""
        return {}
    
    def _extract_industry(self, text: str) -> str:
        """Identify industry from context."""
        return ""
    
    def _extract_priorities(self, text: str) -> List[str]:
        """Extract stated priorities from earnings/interviews."""
        if self.llm:
            # Use LLM to extract
            pass
        return []
    
    def _parse_linkedin(self, text: str) -> Dict[str, Any]:
        """Parse LinkedIn profile info."""
        return {}
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract recent mentions of executive."""
        return []
    
    def _extract_pricing(self, text: str, tool: str) -> Dict[str, Any]:
        """Parse pricing info from search results."""
        # Use LLM to extract: plan names, prices, units
        return {"tool": tool, "source": "web", "confidence": "low"}
    
    def _parse_g2(self, text: str) -> Dict[str, Any]:
        """Parse G2 sentiment from reviews."""
        return {}
    
    def _extract_feature_updates(self, text: str) -> List[str]:
        """Extract recent feature launches."""
        return []
    
    def _extract_weaknesses(self, text: str) -> List[str]:
        """Extract competitive weaknesses from reviews."""
        return []
    
    def _extract_benchmarks(self, text: str, industry: str, metric: str) -> Dict[str, Any]:
        """Extract benchmark numbers."""
        return {}
    
    def _extract_fw_capabilities(self, text: str, product: str, feature: str) -> Dict[str, Any]:
        """Extract company product info."""
        return {}
    
    def _contains_risk_signal(self, texts: List[str], query: str) -> bool:
        """Check if search results indicate a risk signal."""
        return len(texts) > 0
    
    def _classify_risk(self, query: str) -> str:
        """Classify risk type from query."""
        if "layoff" in query:
            return "workforce_reduction"
        elif "budget freeze" in query:
            return "budget_constraint"
        elif "merger" in query or "acquisition" in query:
            return "m&a_risk"
        elif "CIO change" in query or "leadership" in query:
            return "stakeholder_change"
        return "unknown"
