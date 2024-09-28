import os
import pandas as pd
from eventregistry import *
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Initialize EventRegistry with the API key, preventing the use of archive data
er = EventRegistry(apiKey=NEWS_API_KEY, allowUseOfArchive=False)

# Define a query using the QueryArticlesIter for Tesla Inc
q = QueryArticlesIter(
    keywords="Bitcoin",
    sourceLocationUri=QueryItems.OR([
        "http://en.wikipedia.org/wiki/United_Kingdom",
        "http://en.wikipedia.org/wiki/United_States",
        "http://en.wikipedia.org/wiki/Canada"]),
    ignoreSourceGroupUri="paywall/paywalled_sources",
    dataType=["news", "pr"])

# Initialize an empty list to store article data
articles_data = []

# Fetch the most recent 100 articles
for article in q.execQuery(er, sortBy="date", sortByAsc=False, maxItems=500):
    # Get required fields and default to 'N/A' if not available
    title = article.get('title', 'N/A')
    published_on = article.get('dateTimePub', 'N/A')
    source = article.get('source', {}).get('title', 'N/A')
    url = article.get('url', 'N/A')
    
    # Handle the sentiment field safely
    sentiment = article.get('sentiment', 'N/A')
    
    # Check if sentiment is a dictionary or a float
    if isinstance(sentiment, dict):
        sentiment_score = sentiment.get('score', 'N/A')  # Extract the score if available
    else:
        sentiment_score = sentiment  # If it's a float, use it directly

    # Append the article data to the list
    articles_data.append([title, published_on, source, url, sentiment_score])

# Convert the list to a pandas DataFrame
df = pd.DataFrame(articles_data, columns=['Title', 'Published On', 'Source', 'URL', 'Sentiment Score'])

# Save the DataFrame to a CSV file
df.to_csv('tesla_articles_sentiment.csv', index=False)

print("Data saved to 'tesla_articles_sentiment.csv'")
