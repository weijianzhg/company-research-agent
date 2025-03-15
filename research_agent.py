import re
from typing import Dict, List, Any, Optional
import time
from openai import OpenAI
import os
import json
import trafilatura
from ddg import Duckduckgo

class CompanyResearchAgent:
    def __init__(self):
        self.search_delay = 2  # Delay between searches to avoid rate limiting
        self.ddg_api = Duckduckgo()
        self.openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def search_web(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Search the web using DuckDuckGo and extract content
        """
        try:
            search_results = self.ddg_api.search(query)

            if not search_results.get("success"):
                print(f"Search API error for query: {query}")
                return []

            results = []
            if search_results.get("data"):
                for r in search_results["data"][:num_results]:
                    if r.get("url"):
                        try:
                            # Download and extract content from the webpage
                            downloaded = trafilatura.fetch_url(r["url"])
                            if downloaded:
                                text_content = trafilatura.extract(downloaded) or r.get("description", "")
                                results.append({
                                    'title': r.get('title', ''),
                                    'body': text_content,
                                    'link': r["url"]
                                })
                        except Exception:
                            # If content extraction fails, use the search snippet
                            results.append({
                                'title': r.get('title', ''),
                                'body': r.get('description', ''),
                                'link': r["url"]
                            })

            return results

        except Exception as e:
            print(f"Search error details - Query: {query}, Error: {str(e)}")  # Debug info
            return []

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
            print(f"GPT analysis failed: {str(e)}")
            return {'data': 'Analysis failed', 'confidence': 0.0}

    def search_company_profile(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Search and analyze company profile"""
        try:
            # Try multiple search patterns
            search_patterns = [
                company_name,  # Start with just the company name
                f"{company_name} Wikipedia",
                f"{company_name} company",
                f"{company_name} about"
            ]

            for query in search_patterns:
                profile_results = self.search_web(query)
                if profile_results:
                    combined_profile_text = "\n".join([r['body'] for r in profile_results[:3]])
                    profile_analysis = self.analyze_with_gpt(combined_profile_text, company_name, 'profile')

                    if profile_analysis['confidence'] >= 0.3:  # Lower threshold
                        return {
                            'data': profile_analysis['data'],
                            'source': profile_results[0]['link'],
                            'confidence': profile_analysis['confidence']
                        }
                time.sleep(self.search_delay)

            # Return default response if no good results found
            return {'data': 'No reliable profile information found', 'source': 'N/A', 'confidence': 0.0}

        except Exception as e:
            print(f"Profile search error: {str(e)}")
            return {'data': 'Error retrieving profile', 'source': 'N/A', 'confidence': 0.0}

    def search_company_sector(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Search and analyze company sector"""
        try:
            # Try multiple search patterns
            search_patterns = [
                f"{company_name} Wikipedia",
                company_name,
                f"{company_name} sector",
                f"{company_name} industry"
            ]

            for query in search_patterns:
                sector_results = self.search_web(query)
                if sector_results:
                    combined_sector_text = "\n".join([r['body'] for r in sector_results[:3]])
                    sector_analysis = self.analyze_with_gpt(combined_sector_text, company_name, 'sector')

                    if sector_analysis['confidence'] >= 0.3:  # Lower threshold
                        return {
                            'data': sector_analysis['data'],
                            'source': sector_results[0]['link'],
                            'confidence': sector_analysis['confidence']
                        }
                time.sleep(self.search_delay)

            # Return default response if no good results found
            return {'data': 'No reliable sector information found', 'source': 'N/A', 'confidence': 0.0}

        except Exception as e:
            print(f"Sector search error: {str(e)}")
            return {'data': 'Error retrieving sector information', 'source': 'N/A', 'confidence': 0.0}

    def search_company_objectives(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Search and analyze company objectives"""
        try:
            # Try multiple search patterns
            search_patterns = [
                f"{company_name} news",
                f"{company_name} plans",
                f"{company_name} strategy",
                f"{company_name} future"
            ]

            for query in search_patterns:
                objectives_results = self.search_web(query)
                if objectives_results:
                    combined_objectives_text = "\n".join([r['body'] for r in objectives_results[:3]])
                    objectives_analysis = self.analyze_with_gpt(combined_objectives_text, company_name, 'objectives')

                    if objectives_analysis['confidence'] >= 0.3:  # Lower threshold
                        return {
                            'data': objectives_analysis['data'],
                            'source': objectives_results[0]['link'],
                            'confidence': objectives_analysis['confidence']
                        }
                time.sleep(self.search_delay)

            # Return default response if no good results found
            return {'data': 'No reliable objectives information found', 'source': 'N/A', 'confidence': 0.0}

        except Exception as e:
            print(f"Objectives search error: {str(e)}")
            return {'data': 'Error retrieving objectives', 'source': 'N/A', 'confidence': 0.0}

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