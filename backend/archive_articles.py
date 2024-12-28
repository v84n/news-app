import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

class ArticleArchiver:
    def __init__(self, source_file, history_folder):
        self.source_file = source_file
        self.history_folder = history_folder
        self.current_data = None
        self.archive_data = defaultdict(list)
        self.cutoff_date = datetime.utcnow() - timedelta(days=2)

    def setup_history_folder(self):
        """Create history folder if it doesn't exist."""
        if not os.path.exists(self.history_folder):
            os.makedirs(self.history_folder)

    def load_source_file(self):
        """Load the source JSON file."""
        try:
            with open(self.source_file, 'r', encoding='utf-8') as f:
                self.current_data = json.load(f)
        except json.JSONDecodeError as e:
            raise Exception(f"Error reading source file: {str(e)}")
        except FileNotFoundError:
            raise Exception(f"Source file {self.source_file} not found")

    def load_existing_history_file(self, date_str):
        """Load existing history file if it exists."""
        output_file = os.path.join(self.history_folder, f"articles_{date_str}.json")
        existing_articles = []
        
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    existing_articles = existing_data.get('articles', [])
                    print(f"Loaded {len(existing_articles)} existing articles from {output_file}")
            except json.JSONDecodeError as e:
                print(f"Error reading existing archive file {output_file}: {e}")
        
        return existing_articles

    def process_articles(self):
        """Process articles and separate them based on date."""
        current_articles = []
        processed_ids = set()  # Track processed article IDs

        for article in self.current_data.get('articles', []):
            try:
                article_id = article['article_id']
                
                # Skip if we've already processed this article
                if article_id in processed_ids:
                    print(f"Skipping duplicate article ID: {article_id}")
                    continue
                
                processed_ids.add(article_id)
                
                pub_date = datetime.strptime(article['pubDate'], "%Y-%m-%d %H:%M:%S")
                
                if pub_date < self.cutoff_date:
                    # Add to archive
                    date_key = pub_date.strftime("%Y-%m-%d")
                    self.archive_data[date_key].append(article)
                else:
                    # Keep in current file
                    current_articles.append(article)
            
            except (ValueError, KeyError) as e:
                print(f"Error processing article: {str(e)}")
                # Keep articles with invalid dates in current file
                current_articles.append(article)

        return current_articles

    def merge_articles(self, existing_articles, new_articles):
        """Merge existing and new articles, removing duplicates."""
        # Create a dictionary with article_id as key for efficient duplicate removal
        merged_dict = {article['article_id']: article for article in existing_articles}
        
        # Add new articles, overwriting if article_id already exists
        for article in new_articles:
            article_id = article['article_id']
            if article_id in merged_dict:
                print(f"Updating existing article: {article_id}")
            merged_dict[article_id] = article
        
        # Convert back to list and sort by pubDate
        merged_articles = list(merged_dict.values())
        merged_articles.sort(
            key=lambda x: datetime.strptime(x['pubDate'], "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )
        
        return merged_articles

    def save_archive_files(self):
        """Save archived articles to date-specific files."""
        for date_str, new_articles in self.archive_data.items():
            # Load existing articles for this date
            existing_articles = self.load_existing_history_file(date_str)
            
            # Merge existing and new articles
            merged_articles = self.merge_articles(existing_articles, new_articles)
            
            # Save merged articles
            output_file = os.path.join(self.history_folder, f"articles_{date_str}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {'articles': merged_articles},
                    f,
                    ensure_ascii=False,
                    indent=4
                )
            
            print(f"Saved {len(merged_articles)} articles to {output_file}")

    def update_source_file(self, current_articles):
        """Update the source file with remaining current articles."""
        with open(self.source_file, 'w', encoding='utf-8') as f:
            json.dump(
                {'articles': current_articles},
                f,
                ensure_ascii=False,
                indent=4
            )

    def archive_articles(self):
        """Main method to handle the archiving process."""
        try:
            self.setup_history_folder()
            self.load_source_file()
            current_articles = self.process_articles()
            self.save_archive_files()
            self.update_source_file(current_articles)
            
            return {
                'archived_dates': list(self.archive_data.keys()),
                'archived_count': sum(len(articles) for articles in self.archive_data.values()),
                'remaining_count': len(current_articles)
            }
            
        except Exception as e:
            raise Exception(f"Archiving failed: {str(e)}")

def main():
    archiver = ArticleArchiver('latest.json', 'history')
    try:
        results = archiver.archive_articles()
        print("\nArchiving completed successfully:")
        print(f"- Articles archived: {results['archived_count']}")
        print(f"- Articles remaining in latest.json: {results['remaining_count']}")
        print("- Archive dates created/updated:", ', '.join(results['archived_dates']))
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()