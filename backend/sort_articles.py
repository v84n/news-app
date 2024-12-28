import json
import os
from datetime import datetime

class ArticleSorter:
    def __init__(self, source_file):
        self.source_file = source_file
        self.articles = None

    def load_articles(self):
        """Load articles from the source JSON file."""
        try:
            with open(self.source_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.articles = data.get('articles', [])
        except json.JSONDecodeError as e:
            raise Exception(f"Error reading source file: {str(e)}")
        except FileNotFoundError:
            raise Exception(f"Source file {self.source_file} not found")

    def sort_articles(self):
        """Sort articles by pubDate in descending order."""
        try:
            self.articles.sort(
                key=lambda x: datetime.strptime(x['pubDate'], "%Y-%m-%d %H:%M:%S"),
                reverse=True
            )
        except Exception as e:
            raise Exception(f"Error sorting articles: {str(e)}")

    def save_sorted_articles(self):
        """Save the sorted articles back to the file."""
        try:
            with open(self.source_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {'articles': self.articles},
                    f,
                    ensure_ascii=False,
                    indent=4
                )
        except Exception as e:
            raise Exception(f"Error saving sorted articles: {str(e)}")

    def process_file(self):
        """Main method to handle the sorting process."""
        try:
            print(f"\nProcessing file: {self.source_file}")
            self.load_articles()
            original_order = [a['article_id'] for a in self.articles]
            
            self.sort_articles()
            new_order = [a['article_id'] for a in self.articles]
            
            if original_order != new_order:
                self.save_sorted_articles()
                print(f"Articles sorted successfully.")
                print(f"Total articles processed: {len(self.articles)}")
                if len(self.articles) > 0:
                    print(f"Date range: {self.articles[0]['pubDate']} to {self.articles[-1]['pubDate']}")
            else:
                print("Articles were already in correct order.")
            
        except Exception as e:
            print(f"Error: {str(e)}")

def sort_all_files(directory):
    """Sort articles in all JSON files in the given directory."""
    try:
        # Sort latest.json
        if os.path.exists('latest.json'):
            sorter = ArticleSorter('latest.json')
            sorter.process_file()

        # Sort history files
        history_dir = os.path.join(directory, 'history')
        if os.path.exists(history_dir):
            for filename in os.listdir(history_dir):
                if filename.startswith('articles_') and filename.endswith('.json'):
                    file_path = os.path.join(history_dir, filename)
                    sorter = ArticleSorter(file_path)
                    sorter.process_file()

    except Exception as e:
        print(f"Error processing files: {str(e)}")

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sort_all_files(current_dir)

if __name__ == "__main__":
    main()