from duckduckgo_search import DDGS
import re
from typing import Dict, List, Any
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
            results = list(self.ddgs.text(query, max_results=num_results))
            if not results:
                raise Exception(f"No results found for query: {query}")

            # Normalize result fields
            normalized_results = []
            for result in results:
                normalized_results.append({
                    'title': result.get('title', ''),
                    'body': result.get('body', result.get('snippet', '')),
                    'link': result.get('link', result.get('url', ''))
                })
            return normalized_results
        except Exception as e:
            raise Exception(f"Search error: {str(e)}")

    def analyze_with_gpt(self, content: str, company_name: str, analysis_type: str) -> Dict[str, Any]:
        """
        Use GPT to analyze and extract specific company information
        """
        try:
            prompts = {
                'profile': f"Extract a concise company profile for {company_name} from the following text. "
                          f"Focus on what the company does, its main business, and key information. "
                          f"Respond in JSON format with 'data' and 'confidence' fields. "
                          f"Example: {{'data': 'Company profile...', 'confidence': 0.95}}",
                'sector': f"Determine the industry sector and business type of {company_name} from the following text. "
                         f"Be specific about the sector and any sub-sectors. "
                         f"Respond in JSON format with 'data' and 'confidence' fields.",
                'objectives': f"Extract {company_name}'s future objectives, particularly focusing on 2025 goals "
                            f"or strategic plans from the following text. If exact 2025 goals aren't mentioned, "
                            f"include relevant future plans. "
                            f"Respond in JSON format with 'data' and 'confidence' fields."
            }

            response = self.openai.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {"role": "system", "content": "You are a company research analyst focused on extracting accurate information."},
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

    def extract_company_data(self, company_name: str, search_results: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Extract and validate company information from search results using GPT
        """
        # Add more specific search terms for better results
        profile_query = f"{company_name} corporation company profile about business"
        sector_query = f"{company_name} industry sector business type company"
        objectives_query = f"{company_name} company 2025 objectives goals future plans strategy"

        # Initialize results
        results = {
            'profile': {'data': '', 'source': '', 'confidence': 0.0},
            'sector': {'data': '', 'source': '', 'confidence': 0.0},
            'objectives': {'data': '', 'source': '', 'confidence': 0.0}
        }

        try:
            # Extract profile
            profile_results = self.search_web(profile_query)
            time.sleep(self.search_delay)

            # Combine search results for better context
            combined_profile_text = "\n".join([r['body'] for r in profile_results[:3]])
            profile_analysis = self.analyze_with_gpt(combined_profile_text, company_name, 'profile')

            if profile_analysis['confidence'] >= 0.7:
                results['profile'] = {
                    'data': profile_analysis['data'],
                    'source': profile_results[0]['link'],
                    'confidence': profile_analysis['confidence']
                }

            # Extract sector
            sector_results = self.search_web(sector_query)
            time.sleep(self.search_delay)

            combined_sector_text = "\n".join([r['body'] for r in sector_results[:3]])
            sector_analysis = self.analyze_with_gpt(combined_sector_text, company_name, 'sector')

            if sector_analysis['confidence'] >= 0.7:
                results['sector'] = {
                    'data': sector_analysis['data'],
                    'source': sector_results[0]['link'],
                    'confidence': sector_analysis['confidence']
                }

            # Extract objectives
            objectives_results = self.search_web(objectives_query)
            time.sleep(self.search_delay)

            combined_objectives_text = "\n".join([r['body'] for r in objectives_results[:3]])
            objectives_analysis = self.analyze_with_gpt(combined_objectives_text, company_name, 'objectives')

            if objectives_analysis['confidence'] >= 0.7:
                results['objectives'] = {
                    'data': objectives_analysis['data'],
                    'source': objectives_results[0]['link'],
                    'confidence': objectives_analysis['confidence']
                }

            # Validate final results
            if not results['profile']['data']:
                raise Exception(f"Could not find valid profile information for {company_name}")
            if not results['sector']['data']:
                raise Exception(f"Could not find valid sector information for {company_name}")
            if not results['objectives']['data']:
                raise Exception(f"Could not find valid 2025 objectives for {company_name}")

            return results

        except Exception as e:
            raise Exception(f"Data extraction failed: {str(e)}")

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