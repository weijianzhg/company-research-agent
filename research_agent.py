from duckduckgo_search import DDGS
import re
from typing import Dict, List, Any
import time

class CompanyResearchAgent:
    def __init__(self):
        self.search_delay = 2  # Delay between searches to avoid rate limiting
        self.ddgs = DDGS()

    def search_web(self, query: str, num_results: int = 3) -> List[Dict[str, str]]:
        """
        Search the web using DuckDuckGo
        """
        try:
            results = list(self.ddgs.text(query, max_results=num_results))
            return results if results else []
        except Exception as e:
            raise Exception(f"Search error: {str(e)}")

    def validate_data(self, data: str, data_type: str) -> bool:
        """
        Validate extracted data based on type
        """
        if not data:
            return False

        if data_type == 'profile':
            # Profile should be at least 50 characters and mention the company
            return len(data) >= 50
        elif data_type == 'sector':
            # Sector should be a brief description
            return 10 <= len(data) <= 200
        elif data_type == 'objectives':
            # Objectives should mention future plans or 2025
            return '2025' in data or 'future' in data.lower() or 'goal' in data.lower()

        return False

    def extract_company_data(self, company_name: str, search_results: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Extract and validate company information from search results
        """
        profile_query = f"{company_name} company profile about"
        sector_query = f"{company_name} industry sector business"
        objectives_query = f"{company_name} 2025 objectives goals future plans"

        # Initialize results
        results = {
            'profile': {'data': '', 'source': ''},
            'sector': {'data': '', 'source': ''},
            'objectives': {'data': '', 'source': ''}
        }

        # Extract profile
        profile_results = self.search_web(profile_query)
        time.sleep(self.search_delay)

        for result in profile_results:
            if self.validate_data(result['body'], 'profile'):
                results['profile'] = {
                    'data': result['body'],
                    'source': result['link']
                }
                break

        # Extract sector
        sector_results = self.search_web(sector_query)
        time.sleep(self.search_delay)

        for result in sector_results:
            if self.validate_data(result['body'], 'sector'):
                results['sector'] = {
                    'data': result['body'],
                    'source': result['link']
                }
                break

        # Extract objectives
        objectives_results = self.search_web(objectives_query)
        time.sleep(self.search_delay)

        for result in objectives_results:
            if self.validate_data(result['body'], 'objectives'):
                results['objectives'] = {
                    'data': result['body'],
                    'source': result['link']
                }
                break

        # Validate final results
        if not results['profile']['data']:
            raise Exception(f"Could not find valid profile information for {company_name}")
        if not results['sector']['data']:
            raise Exception(f"Could not find valid sector information for {company_name}")
        if not results['objectives']['data']:
            raise Exception(f"Could not find valid 2025 objectives for {company_name}")

        return results

    def research_company(self, company_name: str) -> Dict[str, Any]:
        """
        Main method to research a company
        """
        if not company_name or not isinstance(company_name, str):
            raise ValueError("Invalid company name provided")

        try:
            # Clean company name
            company_name = company_name.strip()

            # Get initial search results
            results = self.extract_company_data(company_name, [])

            return results

        except Exception as e:
            raise Exception(f"Research failed for {company_name}: {str(e)}")