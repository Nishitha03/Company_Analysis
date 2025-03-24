import os
import requests
from bs4 import BeautifulSoup
from newspaper import Article
from urllib.parse import urlparse, quote_plus
import re
import json
import time
import random
import google.generativeai as genai
from collections import Counter
import socket
import dns.resolver
from deep_translator import GoogleTranslator
import gtts
import nltk

# Download NLTK data
nltk.download('punkt_tab')

def configure_dns():
    """Configure DNS resolution to use Google DNS servers"""
    # Use Google's public DNS servers
    dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
    dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4']
    
    # Set socket default timeout
    socket.setdefaulttimeout(30)  # 30 seconds timeout
    
    print("Configured custom DNS resolution with Google DNS servers")

# Call this function before initializing the API
configure_dns()

class NewsExtractor:
    def __init__(self, gemini_api_key):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Initialize Gemini API with error handling and retries
        self.gemini_api_key = gemini_api_key
        genai.configure(api_key=self.gemini_api_key)
        
        # Set up Gemini model with retries
        print("Setting up Gemini API...")
        self.setup_gemini_with_retry()
        
    def setup_gemini_with_retry(self, max_retries=3):
        """Set up Gemini model with retry logic"""
        retry_count = 0
        while retry_count < max_retries:
            try:
                self.model = genai.GenerativeModel('gemini-2.0-flash')
                print("Gemini API setup complete.")
                return
            except Exception as e:
                retry_count += 1
                print(f"Attempt {retry_count} failed: {str(e)}")
                if retry_count < max_retries:
                    print(f"Retrying in {retry_count * 2} seconds...")
                    time.sleep(retry_count * 2)
                else:
                    print("Failed to set up Gemini API after maximum retries.")
                    self.model = None
                    raise

    def query_gemini(self, prompt, max_tokens=500):
        """Query the Gemini model with retry logic."""
        if self.model is None:
            return "Gemini API is not available. Using fallback analysis."
            
        max_retries = 3
        retry_count = 0
        backoff_factor = 2
        
        while retry_count < max_retries:
            try:
                print(f"Generating text with Gemini API (attempt {retry_count + 1})...")
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=max_tokens,
                        temperature=0.7,
                        top_p=0.95,
                        top_k=40,
                    )
                )
                return response.text
                
            except Exception as e:
                retry_count += 1
                error_message = str(e)
                print(f"Error querying Gemini (attempt {retry_count}): {error_message}")
                
                # Handle different types of errors
                if "DNS resolution failed" in error_message or "Timeout" in error_message:
                    # Try to reconfigure DNS for next attempt
                    configure_dns()
                
                if retry_count < max_retries:
                    # Exponential backoff
                    wait_time = backoff_factor ** retry_count
                    print(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print("Failed to query Gemini API after maximum retries.")
                    return "Analysis could not be generated due to API error. Using fallback analysis."

    def translate_to_hindi(self, text):
        """Translate the given text to Hindi."""
        try:
            print("Translating text to Hindi...")
            translator = GoogleTranslator(source='auto', target='hi')
            hindi_text = translator.translate(text)
            print("Translation complete.")
            return hindi_text
        except Exception as e:
            print(f"Error translating to Hindi: {str(e)}")
            return "Hindi translation failed."
    
    def generate_hindi_speech(self, text, output_file="analysis_hindi.mp3"):
        """Generate Hindi speech for the given text."""
        try:
            print("Translating analysis to Hindi...")
            # First translate the text to Hindi
            hindi_text = self.translate_to_hindi(text)
            
            print("Generating Hindi speech...")
            # Generate speech from Hindi text
            tts = gtts.gTTS(text=hindi_text, lang='hi', slow=False)
            
            # Ensure the static folder exists
            os.makedirs('static', exist_ok=True)
            file_path = os.path.join('static', output_file)
            
            tts.save(file_path)
            print(f"Hindi speech generated and saved to {file_path}")
            return file_path, hindi_text
        except Exception as e:
            print(f"Error generating Hindi speech: {str(e)}")
            return None, "Hindi speech generation failed."

    def get_search_results(self, company_name, num_results=15, page=0):
        """Get search results for a company name."""
        start_param = page * 10  # Google uses multiples of 10 for pagination
        search_url = f"https://www.google.com/search?q={quote_plus(company_name)}+news&tbm=nws&start={start_param}"

        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch search results: {str(e)}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        search_results = []

        # Extract news links from Google search results
        for g in soup.find_all('div', class_='SoaBEf'):
            anchor = g.find('a')
            if anchor and 'href' in anchor.attrs:
                link = anchor['href']
                if link.startswith('/url?') or link.startswith('/search?'):
                    link = re.search(r'url\?q=([^&]+)', link)
                    if link:
                        link = link.group(1)

                if link and link.startswith('http'):
                    title_elem = g.find('div', class_='BNeawe vvjwJb AP7Wnd')
                    title = title_elem.text if title_elem else "No title found"

                    snippet_elem = g.find('div', class_='BNeawe s3v9rd AP7Wnd')
                    snippet = snippet_elem.text if snippet_elem else "No snippet found"

                    search_results.append({
                        'title': title,
                        'url': link,
                        'snippet': snippet
                    })

        # Filter out duplicates based on URL
        unique_results = []
        seen_urls = set()

        for result in search_results:
            url = result['url']
            if url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)

                if len(unique_results) >= num_results:
                    break

        return unique_results[:num_results]

    def is_compatible_site(self, url):
        """Check if a website is likely to be scrapable without JS."""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        js_heavy_sites = [
            'twitter.com', 'x.com', 'instagram.com', 'facebook.com',
            'reddit.com', 'linkedin.com', 'youtube.com', 'tiktok.com'
        ]

        return not any(site in domain for site in js_heavy_sites)

    def extract_article_content(self, url):
        """Extract article content from a URL using newspaper3k."""
        try:
            article = Article(url)
            article.download()
            article.parse()
            article.nlp()

            return {
                'title': article.title,
                'text': article.text,
                'summary': article.summary,
                'keywords': article.keywords,
                'publish_date': article.publish_date,
                'success': True
            }
        except Exception as e:
            print(f"Failed to extract content from {url}: {str(e)}")
            return {
                'title': "Extraction failed",
                'text': "",
                'summary': "",
                'keywords': [],
                'publish_date': None,
                'success': False
            }

    def extract_topics_and_summary_combined(self, text):
        """Extract topics, generate a summary, and analyze sentiment using Gemini model in a single query."""
        if not text:
            return [], "No content available for analysis.", "neutral", 0.0
        
        # Limit text to avoid token overflow
        truncated_text = text[:5000]
        
        # SINGLE QUERY: Generate summary, topics and sentiment with Gemini
        combined_prompt = f"""Analyze this article and provide four outputs:
        
        1. SUMMARY: Summarize this article in 3-4 sentences.
        2. TOPICS: Extract 5 key topics (single words or short phrases) from this article. List only the topics separated by commas.
        3. SENTIMENT: Analyze the sentiment of the article (positive, negative, neutral). Only provide 1 word
        4. SENTIMENT_SCORE: Provide a sentiment score between -1 and 1, where -1 is very negative, 0 is neutral, and 1 is very positive.
        
        Format your response as:
        SUMMARY: [your summary here]
        TOPICS: [topic1, topic2, topic3, topic4, topic5]
        SENTIMENT: [positive/negative/neutral]
        SENTIMENT_SCORE: [score]
        
        Article text:
        {truncated_text[:2000]}
        """
        
        combined_response = self.query_gemini(combined_prompt, 300)
        
        # Parse the response
        summary = ""
        topics = []
        sentiment = "neutral"
        sentiment_score = 0.0
        
        summary_match = re.search(r'SUMMARY:(.*?)(?=TOPICS:|$)', combined_response, re.DOTALL)
        if summary_match:
            summary = summary_match.group(1).strip()
        
        topics_match = re.search(r'TOPICS:(.*?)(?=SENTIMENT:|$)', combined_response, re.DOTALL)
        if topics_match:
            topics_text = topics_match.group(1).strip()
            topics = [topic.strip() for topic in topics_text.split(',') if topic.strip()]
        
        sentiment_match = re.search(r'SENTIMENT:(.*?)(?=SENTIMENT_SCORE:|$)', combined_response, re.DOTALL)
        if sentiment_match:
            sentiment = sentiment_match.group(1).strip().lower()
        
        sentiment_score_match = re.search(r'SENTIMENT_SCORE:(.*?)$', combined_response, re.DOTALL)
        if sentiment_score_match:
            try:
                sentiment_score = float(sentiment_score_match.group(1).strip())
            except ValueError:
                sentiment_score = 0.0
        
        # Provide fallbacks if extraction fails
        if not summary or len(summary) < 10:
            if isinstance(text, dict) and 'summary' in text and len(text['summary']) > 10:
                summary = text['summary']
            else:
                sentences = re.split(r'(?<=[.!?])\s+', truncated_text)
                summary = ' '.join(sentences[:3]) if sentences else "No summary available."
        
        if not topics:
            topics = self._extract_keywords(truncated_text, 5)
        
        return topics, summary, sentiment, sentiment_score

    def _extract_keywords(self, text, num_keywords=5):
        """Extract keywords using frequency analysis."""
        # Simple keyword extraction based on frequency
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        stopwords = {'about', 'after', 'also', 'been', 'from', 'have', 'more', 'most', 'other', 'said', 'some', 'that', 'their', 'them', 'then', 'there', 'these', 'they', 'this', 'were', 'what', 'when', 'which', 'with', 'would'}
        filtered_words = [w for w in words if w not in stopwords]
        
        # Count word frequency
        word_counts = {}
        for word in filtered_words:
            if word in word_counts:
                word_counts[word] += 1
            else:
                word_counts[word] = 1
        
        # Get top keywords
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:num_keywords]]

    def extract_and_analyze(self, company_name, max_articles=10):
        """Extract news articles about a company and analyze their content."""
        print(f"Searching for news about {company_name}...")

        articles_data = []
        counter = 0
        page = 0
        max_pages = 5  # Limit to 5 pages of results to avoid excessive requests

        while counter < max_articles and page < max_pages:
            print(f"Fetching page {page+1} of Google News results...")
            search_results = self.get_search_results(company_name, num_results=max_articles+5, page=page)

            if not search_results:
                print(f"No more results found on page {page+1}")
                break

            for result in search_results:
                if counter >= max_articles:
                    break

                url = result['url']
                print(f"Processing article {counter+1}: {url}")

                if not self.is_compatible_site(url):
                    print(f"Skipping potentially JS-heavy site: {url}")
                    continue

                article_content = self.extract_article_content(url)

                if not article_content['success'] or not article_content['text']:
                    print(f"Could not extract content from {url}")
                    continue

                # Extract topics and summary using Gemini in a single query
                topics, summary, sentiment, sentiment_score = self.extract_topics_and_summary_combined(article_content['text'])

                articles_data.append({
                    'title': article_content['title'],
                    'url': url,
                    'summary': summary,
                    'topics': topics,
                    'sentiment': sentiment,
                    'sentiment_score': sentiment_score,
                    'text': article_content['text'][:5000],  # Limit text size for storage
                    'publish_date': article_content['publish_date'],
                })

                counter += 1
                time.sleep(random.uniform(1, 3))

            if counter < max_articles:
                page += 1
                print(f"Only {counter} articles processed so far, moving to page {page+1}...")
                time.sleep(random.uniform(3, 5))
            else:
                break

        print(f"Processed a total of {counter} articles across {page+1} pages.")
        return articles_data

    def _normalize_dates(self, dates):
        """Convert all dates to naive UTC datetime objects for comparison."""
        from datetime import timezone
        
        normalized_dates = []
        for date in dates:
            if date is None:
                continue
                
            # If the date is timezone-aware, convert to UTC and remove timezone info
            if date.tzinfo is not None:
                normalized_date = date.astimezone(timezone.utc).replace(tzinfo=None)
            else:
                # If date is already naive, use as is
                normalized_date = date
                
            normalized_dates.append(normalized_date)
        
        return normalized_dates

    def generate_article_comparison(self, articles_data):
        """Generate a comparison between articles without using LLM."""
        if not articles_data or len(articles_data) < 2:
            return {
                "comparison": "Not enough articles to compare.",
                "topics": {}
            }
        
        # Collect all topics from all articles
        all_topics = []
        for article in articles_data:
            all_topics.extend(article.get('topics', []))
        
        # Count frequency of each topic
        topic_counter = Counter(all_topics)
        common_topics = topic_counter.most_common()
        
        # Find shared topics (appear in at least 2 articles)
        shared_topics = {topic: count for topic, count in common_topics if count >= 2}
        
        # Find unique topics (appear in only 1 article)
        unique_topics = {topic: count for topic, count in common_topics if count == 1}
        
        # Generate comparison text
        comparison_text = "Article Comparison:\n"
        
        if shared_topics:
            topic_percentage = len(shared_topics) / len(common_topics) * 100 if common_topics else 0
            comparison_text += f"The articles share {len(shared_topics)} common topics ({topic_percentage:.1f}% of all topics). "
            
            # Analyze how consistent the coverage is
            if topic_percentage > 70:
                comparison_text += "The coverage is highly consistent across sources. "
            elif topic_percentage > 40:
                comparison_text += "The coverage shows moderate consistency across sources. "
            else:
                comparison_text += "The coverage varies significantly across sources. "
        else:
            comparison_text += "There are no shared topics between articles, indicating diverse or contradictory coverage. "
        
        # Look for potential contradictions or different angles
        if len(articles_data) >= 3 and shared_topics:
            comparison_text += "Despite covering similar topics, the articles may present different perspectives or emphasize different aspects. "
        
        # Compare publication dates if available
        dates = []
        for article in articles_data:
            if article.get('publish_date'):
                dates.append(article.get('publish_date'))

        if dates and len(dates) >= 2:
            normalized_dates = self._normalize_dates(dates)
            if normalized_dates and len(normalized_dates) >= 2:
                date_range = max(normalized_dates) - min(normalized_dates)
                if date_range.days > 7:
                    comparison_text += f"The articles span a {date_range.days}-day period, suggesting evolving coverage over time."
                else:
                    comparison_text += "The articles were published within a short timeframe, representing contemporary perspectives."
          
        return {
            "comparison": comparison_text,
            "topics": {
                "shared": dict(sorted(shared_topics.items(), key=lambda x: x[1], reverse=True)),
                "unique": dict(sorted(unique_topics.items(), key=lambda x: x[1], reverse=True))
            }
        }

    def analyze_articles_manually(self, company_name, articles_data):
        """Generate analysis without using the API when it's not working properly."""
        # Collect all topics
        all_topics = []
        for article in articles_data:
            all_topics.extend(article['topics'])
        
        # Count frequency
        topic_counts = {}
        for topic in all_topics:
            if topic in topic_counts:
                topic_counts[topic] += 1
            else:
                topic_counts[topic] = 1
        
        # Get top topics
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        top_topics = [topic for topic, count in sorted_topics[:5]]
        
        # Generate simple analysis
        analysis = f"""
        Analysis of recent news about {company_name}:
        
        Key topics found across articles: {', '.join(top_topics)}.
        
        The news coverage appears to focus on these main areas, indicating 
        these are currently the most relevant aspects of {company_name}'s 
        business or operations in the public discourse.
        
        Most recent articles discuss {articles_data[0]['topics'][0] if articles_data and 'topics' in articles_data[0] and articles_data[0]['topics'] else 'various business developments'}.
        
        For a comprehensive understanding, review the individual article summaries.
        """
        
        return analysis

    def format_data_for_output(self, company_name, articles_data):
        """Format the data into the requested output format."""
        if not articles_data:
            return {
                "Company": company_name,
                "Articles": [],
                "LLM Analysis": f"No articles were found for {company_name}.",
                "Comparison": {
                    "comparison": "No articles to compare.",
                    "topics": {}
                }
            }

        # Format articles
        formatted_articles = []
        for article in articles_data:
            formatted_articles.append({
                "Title": article['title'],
                "URL": article['url'],
                "sentiment" : article['sentiment'],
                "sentiment_score" : article['sentiment_score'],
                "Summary": article['summary'],
                "Topics": article['topics'],
                "Publish Date": str(article['publish_date']) if article['publish_date'] else "Unknown"
            })

        # Generate comparison between articles
        comparison = self.generate_article_comparison(articles_data)

        try:
            # Generate analysis with Gemini
            analysis_prompt = f"""You are analyzing news about {company_name}. Based on these article summaries, identify the key trends, sentiment, and business implications. 
            Keep your analysis concise but insightful, focusing on what these news items reveal about the company's current situation and potential future. keep it 1-2 lines long only.
            
            Article summaries:
            """
            
            # Add article summaries
            for i, article in enumerate(formatted_articles[:7]):  # Gemini can handle more articles
                analysis_prompt += f"\nArticle {i+1}: {article['Title']}. {article['Summary']}\n"
            
            final_analysis = self.query_gemini(analysis_prompt, 500)
            
            if not final_analysis or len(final_analysis) < 50:
                # Fallback to rule-based analysis
                print("Gemini analysis failed, using rule-based analysis...")
                final_analysis = self.analyze_articles_manually(company_name, articles_data)
        except Exception as e:
            print(f"Error generating analysis: {str(e)}")
            final_analysis = self.analyze_articles_manually(company_name, articles_data)

        return {
            "Company": company_name,
            "Articles": formatted_articles,
            "LLM Analysis": final_analysis,
            "Comparison": comparison
        }