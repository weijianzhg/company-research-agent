from duckduckgo_search import DDGS
import re
from typing import Dict, List, Any, Optional
import time
from openai import OpenAI
import os
import json

class CompanyResearchAgent:
    def __init__(self):
        self.search_delay = 2  # Delay between searches to avoid rate limiting
        self.ddgs = DDGS()
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Search the web using DuckDuckGo
        """
        try:
            # Add company-specific terms to improve search relevance
            enhanced_query = f"{query} site:bloomberg.com OR site:reuters.com OR site:forbes.com"
            results = list(self.ddgs.text(enhanced_query, max_results=num_results))

            if not results:
                # Try without site restrictions if no results found
                results = list(self.ddgs.text(query, max_results=num_results))
                if not results:
                    raise Exception(f"No results found for query: {query}")

            # Normalize result fields and ensure valid URLs
            normalized_results = []
            for result in results:
                if result.get('link') or result.get('url'):
                    normalized_results.append({
                        'title': result.get('title', ''),
                        'body': result.get('body', result.get('snippet', '')),
                        'link': result.get('link') or result.get('url', '')
                    })

            if not normalized_results:
                raise Exception(f"No valid results with source URLs found for query: {query}")

            return normalized_results

        except Exception as e:
            print(f"Search error details - Query: {query}, Error: {str(e)}")  # Debug info
            raise Exception(f"Search error: {str(e)}")

    def analyze_with_gpt(self, content: str, company_name: str, analysis_type: str) -> Dict[str, Any]:
        """
        Use GPT to analyze and extract specific company information
        """
        try:
            prompts = {
                'profile': f"Extract a concise company profile for {company_name} from the following text. "
                          f"Focus on what the company does, its main business, and key information. "
                          f"Be concise but comprehensive. If uncertain, provide the most reliable information found. "
                          f"Respond in JSON format with 'data' and 'confidence' fields.",
                'sector': f"Determine the industry sector and business type of {company_name} from the following text. "
                         f"Be specific about the sector and any sub-sectors. If multiple sectors are found, list the primary ones. "
                         f"Respond in JSON format with 'data' and 'confidence' fields. "
                         f"Example: {{'data': 'Technology - Consumer Electronics, Software, and Services', 'confidence': 0.95}}",
                'objectives': f"Extract {company_name}'s future objectives, particularly focusing on 2025 goals "
                            f"or strategic plans from the following text. If exact 2025 goals aren't mentioned, "
                            f"include relevant future plans or recent strategic initiatives. "
                            f"Respond in JSON format with 'data' and 'confidence' fields."
            }

            response = self.openai.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {"role": "system", "content": "You are a company research analyst focused on extracting accurate information. Always provide information if found, with appropriate confidence levels."},
                    {"role": "user", "content": f"{prompts[analysis_type]}\n\nText: {content}"}
                ],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Validate and convert confidence to float
            if not isinstance(result, dict):
                raise ValueError("GPT response is not a dictionary")
            if 'data' not in result or 'confidence' not in result:
                raise ValueError("GPT response missing required fields")

            # Ensure confidence is a float between 0 and 1
            try:
                result['confidence'] = float(result['confidence'])
                result['confidence'] = max(0.0, min(1.0, result['confidence']))
            except (ValueError, TypeError):
                result['confidence'] = 0.0

            return result

        except Exception as e:
            raise Exception(f"GPT analysis failed: {str(e)}")

    def search_company_profile(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Search and analyze company profile"""
        profile_query = f"{company_name} company about business description overview"
        profile_results = self.search_web(profile_query)
        time.sleep(self.search_delay)

        if not profile_results:
            return None

        combined_profile_text = "\n".join([r['body'] for r in profile_results[:3]])
        profile_analysis = self.analyze_with_gpt(combined_profile_text, company_name, 'profile')

        if profile_analysis['confidence'] >= 0.3:  # Lower threshold
            return {
                'data': profile_analysis['data'],
                'source': profile_results[0]['link'],
                'confidence': profile_analysis['confidence']
            }
        return None

    def search_company_sector(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Search and analyze company sector"""
        sector_query = f"{company_name} industry sector business type"
        sector_results = self.search_web(sector_query)
        time.sleep(self.search_delay)

        if not sector_results:
            return None

        combined_sector_text = "\n".join([r['body'] for r in sector_results[:3]])
        sector_analysis = self.analyze_with_gpt(combined_sector_text, company_name, 'sector')

        if sector_analysis['confidence'] >= 0.3:  # Lower threshold
            return {
                'data': sector_analysis['data'],
                'source': sector_results[0]['link'],
                'confidence': sector_analysis['confidence']
            }
        return None

    def search_company_objectives(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Search and analyze company objectives"""
        objectives_query = f"{company_name} corporate goals strategy future plans news"
        objectives_results = self.search_web(objectives_query)
        time.sleep(self.search_delay)

        if not objectives_results:
            return None

        combined_objectives_text = "\n".join([r['body'] for r in objectives_results[:3]])
        objectives_analysis = self.analyze_with_gpt(combined_objectives_text, company_name, 'objectives')

        if objectives_analysis['confidence'] >= 0.3:  # Lower threshold
            return {
                'data': objectives_analysis['data'],
                'source': objectives_results[0]['link'],
                'confidence': objectives_analysis['confidence']
            }
        return None

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
            profile_data = self.search_company_profile(company_name)
            time.sleep(self.search_delay)  # Add delay between searches

            sector_data = self.search_company_sector(company_name)
            time.sleep(self.search_delay)

            objectives_data = self.search_company_objectives(company_name)

            results = {
                'profile': profile_data if profile_data else {'data': 'Not found', 'source': 'N/A', 'confidence': 0.0},
                'sector': sector_data if sector_data else {'data': 'Not found', 'source': 'N/A', 'confidence': 0.0},
                'objectives': objectives_data if objectives_data else {'data': 'Not found', 'source': 'N/A', 'confidence': 0.0}
            }

            return results

        except Exception as e:
            raise Exception(f"Research failed for {company_name}: {str(e)}")