"""
Web Search Utility - Provides search capabilities for bees.

Uses "malicious compliance" to find high-value targets by scraping
search engine results for commercial intent keywords.
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict, Any
from urllib.parse import urlparse
import re

class WebSearch:
    """
    Search engine scraper focused on finding commercial entities.
    """

    BASE_URL = "https://html.duckduckgo.com/html/"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://duckduckgo.com/"
    }

    @staticmethod
    def search(query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform a web search and return parsed results.
        """
        try:
            # Sleep briefly to avoid aggressive rate limiting
            time.sleep(random.uniform(1.0, 3.0))

            payload = {'q': query}
            response = requests.post(WebSearch.BASE_URL, data=payload, headers=WebSearch.HEADERS, timeout=10)
            response.raise_for_status()

            return WebSearch._parse_ddg_html(response.text, num_results)

        except Exception as e:
            print(f"[WebSearch] Error searching for '{query}': {e}")
            return []

    @staticmethod
    def _parse_ddg_html(html: str, limit: int) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo HTML results."""
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        # DDG HTML structure selectors
        result_divs = soup.find_all('div', class_='result')

        for div in result_divs:
            if len(results) >= limit:
                break

            try:
                # Title and Link
                title_tag = div.find('a', class_='result__a')
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                link = title_tag.get('href')

                # Snippet
                snippet_tag = div.find('a', class_='result__snippet')
                snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

                # Filter out generic or non-useful links
                if WebSearch._is_ignored_domain(link):
                    continue

                results.append({
                    "title": title,
                    "url": link,
                    "snippet": snippet,
                    "domain": urlparse(link).netloc
                })

            except Exception:
                continue

        return results

    @staticmethod
    def _is_ignored_domain(url: str) -> bool:
        """Filter out non-commercial or generic domains."""
        ignored = [
            "wikipedia.org",
            "amazon.com",
            "facebook.com",
            "twitter.com",
            "instagram.com",
            "linkedin.com",
            "pinterest.com",
            "youtube.com",
            "reddit.com",
            "quora.com",
            "duckduckgo.com",
            "medium.com",
            "forbes.com",
            "businessinsider.com",
            "nytimes.com"
        ]
        domain = urlparse(url).netloc
        # Check against ignored list
        if any(x in domain for x in ignored):
            return True
        return False

    @staticmethod
    def find_brands_for_category(category: str) -> List[Dict[str, Any]]:
        """
        Find potential sponsor brands for a category using aggressive commercial queries.
        """
        # Clean category name for search (remove underscores)
        search_cat = category.replace("_", " ")

        # "Malicious compliance" queries - targeting money and direct company pages
        # Mixed strategy: some listicles (high signal), some direct product pages
        queries = [
            f'"{search_cat}" "pricing" "features" -"best" -"top"', # Attempt to find product pages
            f'"{search_cat}" "solutions" "contact sales"',
            f'"{search_cat}" "book a demo"',
            f'site:.com "{search_cat}" "partners"',
            f'top {search_cat} companies affiliate program' # Fallback to aggregators
        ]

        all_results = []
        seen_domains = set()

        # Pick one random query strategy
        query = random.choice(queries)
        print(f"[WebSearch] Scouting with query: {query}")

        results = WebSearch.search(query, num_results=10)

        for res in results:
            domain = res['domain']
            if domain not in seen_domains:
                seen_domains.add(domain)

                # Clean title to get company name estimate
                company_name = WebSearch._extract_company_name(res['title'], domain)

                res['category'] = category
                res['company'] = company_name
                res['estimated_value'] = WebSearch._infer_value(res['snippet'])
                all_results.append(res)

        return all_results

    @staticmethod
    def _extract_company_name(title: str, domain: str) -> str:
        """Attempt to extract a cleaner company name from title."""
        # Split by common separators | - :
        parts = re.split(r'[|\-:]', title)
        # Usually the brand is at the start or end.
        # If the domain name is in one of the parts, that's a good guess.

        domain_root = domain.replace("www.", "").split(".")[0]

        for part in parts:
            clean_part = part.strip()
            if domain_root.lower() in clean_part.lower():
                return clean_part

        # Fallback: First part
        return parts[0].strip()

    @staticmethod
    def _infer_value(snippet: str) -> str:
        """Guess the value of the prospect based on keywords."""
        snippet = snippet.lower()
        high_value_keywords = ["enterprise", "solution", "global", "leader", "funded", "series a", "series b", "platform", "ai", "automated"]
        low_value_keywords = ["blog", "review", "free", "cheap", "diy", "hobby"]

        if any(k in snippet for k in high_value_keywords):
            return "high"
        if any(k in snippet for k in low_value_keywords):
            return "low"
        return "medium"

if __name__ == "__main__":
    # Quick test
    print("Testing WebSearch...")
    brands = WebSearch.find_brands_for_category("music_tech")
    for b in brands:
        print(f"- {b['company']} ({b['url']}) [{b['estimated_value']}]")
