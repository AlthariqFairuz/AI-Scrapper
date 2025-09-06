import requests
from bs4 import BeautifulSoup
import json
import argparse
from typing import Dict, List, Optional
import re
from dataclasses import dataclass
from openai import OpenAI
from urllib.parse import urljoin
import time
import dotenv

OPENROUTER_API_KEY = dotenv.get_key('.env', 'OPENROUTER_API_KEY')

@dataclass
class SearchParams:
    """Data class for search parameters"""
    state: Optional[str] = None
    member: Optional[str] = None
    breed: Optional[str] = None

class Scrapper:
    """Scraper class"""
    
    def __init__(self, base_url: str = "https://www.amgr.org/frm_directorySearch.cfm"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.openrouter_client = None
        self._setup_openrouter()
    
    def _setup_openrouter(self):

        try:
            self.openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key= OPENROUTER_API_KEY
            )

        except Exception as e:
            print(f"Error: {e}")
            return {}
    
    def parse_natural_language(self, command: str) -> SearchParams:
        """Parse natural language command using OpenRouter API"""
        if not self.openrouter_client:
            print("OpenRouter API not configured. Please set OPENROUTER_API_KEY environment variable.")
            return SearchParams()
                
        try:
            prompt = f"""
            Parse the following natural language command into search parameters for an AMGR Directory search.
            Extract state, member name, and breed information if mentioned.

            Command: "{command}"

            Return a JSON object with keys: state, member, breed
            If a parameter is not mentioned, set it to null.
            
            Example response:
            {{"state": "Kansas", "member": "Dwight Elmore", "breed": "(AR) - American Red"}}
            """
            
            response = self.openrouter_client.chat.completions.create(
                model="deepseek/deepseek-r1-distill-llama-70b:free",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that parses natural language commands into structured search parameters. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                parsed_data = json.loads(json_match.group())
                return SearchParams(
                    state=parsed_data.get('state'),
                    member=parsed_data.get('member'),
                    breed=parsed_data.get('breed')
                )
            
        except Exception as e:
            print(f"Error parsing natural language command: {e}")
        
        return SearchParams()
    
    def _check_pagination(self, soup: BeautifulSoup) -> Dict[str, any]:

        pagination_info = {
            'has_pagination': False,
            'current_page': 1,
            'total_pages': 1,
            'next_enabled': False,
            'next_page': None
        }
        
        pagination = soup.find('ul', class_='pagination')
        if not pagination:
            return pagination_info
        
        pagination_info['has_pagination'] = True
        
        # find current page (active)
        active_page = pagination.find('li', class_='active')
        if active_page:
            page_link = active_page.find('a')
            if page_link:
                pagination_info['current_page'] = int(page_link.get_text().strip())
        
        # find next button
        next_button = pagination.find('li', id=lambda x: x and x.endswith('_next'))
        if next_button and 'disabled' not in next_button.get('class', []):
            pagination_info['next_enabled'] = True
            next_link = next_button.find('a')
            if next_link:
                pagination_info['next_page'] = next_link.get('data-dt-idx')
        
        page_links = pagination.find_all('a', {'data-dt-idx': True})
        max_page = 1
        for link in page_links:
            try:
                page_num = int(link.get_text().strip())
                max_page = max(max_page, page_num)
            except (ValueError, AttributeError):
                continue
        pagination_info['total_pages'] = max_page
        
        return pagination_info
    
    def _navigate_to_page(self, page_number: int, form_data: Dict) -> Optional[BeautifulSoup]:
        try:
            
            form_data_copy = form_data.copy()
            form_data_copy['page'] = str(page_number)
            
            response = self.session.post(self.base_url, data=form_data_copy)
            response.raise_for_status()
            
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error navigating to page {page_number}: {e}")
            return None
    
    def perform_search(self, params: SearchParams, max_pages: int = 10) -> List[Dict]:
        """Perform search with given parameters, handling pagination"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            form_data = {}
            
            for input_elem in soup.find_all('input'):
                name = input_elem.get('name')
                if name:
                    form_data[name] = input_elem.get('value', '')
            
            for select_elem in soup.find_all('select'):
                name = select_elem.get('name')

                if name:
                    if params.state and name == 'stateID':
                        value = self._find_option_value(select_elem, params.state)
                        form_data[name] = value
                    elif params.member and name == 'memberID':
                        value = self._find_option_value(select_elem, params.member)
                        form_data[name] = value
                    elif params.breed and name == 'breedID':
                        value = self._find_option_value(select_elem, params.breed)
                        form_data[name] = value
                    else:
                        # default use empty value
                        empty_option = select_elem.find('option', value="")
                        if empty_option:
                            form_data[name] = ""

            response = self.session.post(self.base_url, data=form_data)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            all_results = []
            
            page_results = self._parse_results(response.content)
            all_results.extend(page_results)
            
            pagination_info = self._check_pagination(soup)
            
            if pagination_info['has_pagination'] and pagination_info['total_pages'] > 1:
                print(f"Total pages: {pagination_info['total_pages']}")
                
                current_page = pagination_info['current_page']
                pages_processed = 1
                
                while pages_processed < max_pages and pagination_info['next_enabled']:
                    current_page += 1
                    
                    next_soup = self._navigate_to_page(current_page, form_data)
                    if not next_soup:
                        break
                    
                    page_results = self._parse_results(str(next_soup).encode())
                    all_results.extend(page_results)
                    print(f"Found {len(page_results)} results on page {current_page}")
                    
                    pagination_info = self._check_pagination(next_soup)
                    pages_processed += 1
                    
                    time.sleep(1)
                    
                    if not pagination_info['next_enabled']:
                        break
            
            print(f"Total results collected: {len(all_results)}")
            return all_results
            
        except requests.RequestException as e:
            print(f"Error performing search: {e}")
            return []
    
    def _find_option_value(self, select_elem, target_text: str) -> str:
        """Find the value for a select option that matches the target text"""

        # exact matches only
        for option in select_elem.find_all('option'):
            option_text = option.get_text().strip()
            option_value = option.get('value', '')
            
            # case insensitive
            if target_text.lower() == option_text.lower():
                return option_value
                
            # direct value match
            if target_text == option_value:
                return option_value
        
        # word boundary matches
        for option in select_elem.find_all('option'):
            option_text = option.get_text().strip()
            option_value = option.get('value', '')
            
            pattern = r'\b' + re.escape(target_text.lower()) + r'\b'
            if re.search(pattern, option_text.lower()):
                return option_value
        
        return ''
    
    def _parse_results(self, html_content: bytes) -> List[Dict]:
        """Parse search results from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        results = []
        
        # look for result tables
        tables = soup.find_all('table')
        
        for table in tables:
            headers = []
            
            thead = table.find('thead')
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
        
            if not headers:
                continue
            
            data_rows = []
            tbody = table.find('tbody')
            if tbody:
                data_rows = tbody.find_all('tr')
            
            for row in data_rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= len(headers):
                    row_data = {}
                    for i, cell in enumerate(cells[:len(headers)]):
                        cell_text = cell.get_text().strip()
                        # check for links
                        link = cell.find('a')
                        if link and link.get('href'):
                            href = link.get('href')
                            #  make  URL absolute
                            if href.startswith('/') or not href.startswith('http'):
                                href = urljoin(self.base_url, href)
                            cell_text = f"{cell_text} [{href}]"
                        
                        row_data[headers[i]] = cell_text
                    
                    if any(row_data.values()):  
                        results.append(row_data)
        
        return results
    
    def display_results(self, results: List[Dict]):
        if not results:
            print("No results found.")
            return
        
        headers = list(results[0].keys())
        
        # column widths
        col_widths = {}
        for header in headers:
            col_widths[header] = max(len(header), max(len(str(row.get(header, ''))) for row in results))
        
        # header
        header_line = " | ".join(header.ljust(col_widths[header]) for header in headers)
        print(header_line)
        print("-" * len(header_line))
        
        # data rows
        for row in results:
            data_line = " | ".join(str(row.get(header, '')).ljust(col_widths[header]) for header in headers)
            print(data_line)

def main():
    parser = argparse.ArgumentParser(description='AMGR Directory Search CLI Scraper with Pagination')
    parser.add_argument('--state', help='State to search for')
    parser.add_argument('--member', help='Member name to search for')
    parser.add_argument('--breed', help='Breed to search for')
    parser.add_argument('--natural', help='Natural language command')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')
    
    args = parser.parse_args()
    
    scraper = Scrapper()

    if args.interactive:
        print("AMGR Directory Search - Interactive Mode")
        print("Enter natural language commands or 'quit' to exit")
        print("Example: 'Find members in Kansas with American Red breed'")
        
        while True:
            try:
                command = input("\n> ").strip()
                if command.lower() in ['quit', 'exit', 'q']:
                    break
                
                if command:
                    params = scraper.parse_natural_language(command)
                    print(f"Searching: State={params.state}, Member={params.member}, Breed={params.breed}")
                    
                    results = scraper.perform_search(params)
                    scraper.display_results(results)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
        return
    
    if args.natural:
        params = scraper.parse_natural_language(args.natural)
        print(f"Parsed from natural language: State={params.state}, Member={params.member}, Breed={params.breed}")
    else:
        params = SearchParams(
            state=args.state,
            member=args.member,
            breed=args.breed
        )
    
    if args.natural or any([params.state, params.member, params.breed]):
        results = scraper.perform_search(params)
        scraper.display_results(results)
    else:
        print("No search parameters provided. Use --help for usage information.")
        
        print("\nExample commands:")
        print("python scraper.py --state Kansas --member 'Dwight Elmore'")
        print("python scraper.py --natural 'Find members in Kansas with American Red breed'")
        print("python scraper.py --interactive")

if __name__ == "__main__":
    main()