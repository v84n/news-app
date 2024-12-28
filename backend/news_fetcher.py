import json
import requests
import time
from datetime import datetime
import os

class NewsArticleFetcher:
    def __init__(self, base_url, output_file):
        self.base_url = base_url
        self.output_file = output_file
        self.existing_articles = self.load_existing_articles()
        self.initial_article_ids = set(article['article_id'] for article in self.existing_articles['articles'])

    def load_existing_articles(self):
        """Load existing articles from the JSON file or create new structure if file doesn't exist."""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error reading {self.output_file}, creating new structure")
        return {"articles": []}

    def save_articles(self):
        """Save articles to the JSON file."""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.existing_articles, f, ensure_ascii=False, indent=4)

    def update_article(self, new_article):
        """Update or append an article in the existing articles list."""
        for i, article in enumerate(self.existing_articles['articles']):
            if article['article_id'] == new_article['article_id']:
                self.existing_articles['articles'][i] = new_article
                return
        self.existing_articles['articles'].append(new_article)

    def fetch_articles(self):
        """Main method to fetch articles from the API."""
        next_page = None
        request_count = 0
        max_requests = 2

        while request_count < max_requests:
            # Construct URL
            url = self.base_url
            if next_page:
                url = f"{url}&page={next_page}"

            try:
                # Make API request with error handling and retry mechanism
                response = self.make_api_request(url)
                
                if not response or response.get('status') != 'success':
                    print(f"Error in API response: {response}")
                    break

                # Process articles
                found_old_article = False
                for article in response.get('results', []):
                    if article['article_id'] in self.initial_article_ids:
                        found_old_article = True
                        break
                    self.update_article(article)

                # Save after each successful request
                self.save_articles()

                if found_old_article:
                    print("Found existing article, stopping fetch")
                    break

                next_page = response.get('nextPage')
                if not next_page:
                    print("No more pages available")
                    break

                request_count += 1
                time.sleep(5)  # Rate limiting

            except Exception as e:
                print(f"Error during fetch: {str(e)}")
                break

    def make_api_request(self, url, max_retries=3):
        """Make API request with retry mechanism."""
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.RequestException as e:
                print(f"Request failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        return None

def main():
    base_url = "https://newsdata.io/api/1/latest?apikey=pub_6288297c1f10537fb134848f54aece832859b&country=in,us&language=en,hi"
    output_file = "latest.json"
    
    fetcher = NewsArticleFetcher(base_url, output_file)
    fetcher.fetch_articles()

if __name__ == "__main__":
    main()