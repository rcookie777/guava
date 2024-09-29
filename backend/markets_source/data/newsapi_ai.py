import os
import pandas as pd
from eventregistry import *
from dotenv import load_dotenv

# Load the API key from the .env file
load_dotenv()
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_articles_by_keyword(keyword, max_items=100, save_to_csv=False, csv_filename=None):
    """
    Fetches articles related to a specific keyword using the EventRegistry API and returns the results as a pandas DataFrame.
    """
    if not NEWS_API_KEY:
        raise ValueError("NEWS_API_KEY not found in the environment variables.")
    
    # Initialize EventRegistry with the API key, preventing the use of archive data
    er = EventRegistry(apiKey=NEWS_API_KEY, allowUseOfArchive=False)

    # Define a query using the keyword provided as input
    q = QueryArticlesIter(
        keywords=keyword,
        sourceLocationUri=QueryItems.OR([
            "http://en.wikipedia.org/wiki/United_Kingdom",
            "http://en.wikipedia.org/wiki/United_States",
            "http://en.wikipedia.org/wiki/Canada"]),
        ignoreSourceGroupUri="paywall/paywalled_sources",
        dataType=["news", "pr"])

    # Initialize an empty list to store article data
    articles_data = []

    # Fetch the most recent articles
    for article in q.execQuery(er, sortBy="date", sortByAsc=False, maxItems=max_items):
        title = article.get('title', 'N/A')
        published_on = article.get('dateTimePub', 'N/A')
        source = article.get('source', {}).get('title', 'N/A')
        url = article.get('url', 'N/A')

        # Handle the sentiment field safely
        sentiment = article.get('sentiment', 'N/A')
        sentiment_score = sentiment.get('score', 'N/A') if isinstance(sentiment, dict) else sentiment

        # Append the article data to the list
        articles_data.append([title, published_on, source, url, sentiment_score])

    # Convert the list to a pandas DataFrame
    df = pd.DataFrame(articles_data, columns=['Title', 'Published On', 'Source', 'URL', 'Sentiment Score'])

    # Optionally save the DataFrame to a CSV file
    if save_to_csv and csv_filename:
        df.to_csv(csv_filename, index=False)
        print(f"Data saved to '{csv_filename}'")

    return df


def get_events_by_concept(concept_uri, max_items=50, save_to_csv=False, csv_filename=None):
    """
    Fetches events related to a specific concept using the EventRegistry API and returns the results as a pandas DataFrame.
    """
    if not NEWS_API_KEY:
        raise ValueError("NEWS_API_KEY not found in the environment variables.")
    
    # Initialize EventRegistry with the API key
    er = EventRegistry(apiKey=NEWS_API_KEY, allowUseOfArchive=False)

    # Define a query using the concept URI provided as input
    q = QueryEventsIter(conceptUri=concept_uri)

    # Initialize an empty list to store event data
    events_data = []

    # Fetch the most relevant events
    for event in q.execQuery(er, sortBy="rel", maxItems=max_items):
        event_title = event.get('title', {}).get('eng', 'N/A')
        event_date = event.get('eventDate', 'N/A')
        event_uri = event.get('uri', 'N/A')
        event_category = event.get('categories', 'N/A')
        
        # Handle missing location safely
        location = event.get('location', {})
        event_location = location.get('label', {}).get('eng', 'N/A') if location else 'N/A'

        # Append the event data to the list
        events_data.append([event_title, event_date, event_uri, event_category, event_location])

    # Convert the list to a pandas DataFrame
    df = pd.DataFrame(events_data, columns=['Title', 'Event Date', 'Event URI', 'Categories', 'Location'])

    # Optionally save the DataFrame to a CSV file
    if save_to_csv and csv_filename:
        df.to_csv(csv_filename, index=False)
        print(f"Data saved to '{csv_filename}'")

    return df


def get_concept_uri(keyword):
    """
    Uses the EventRegistry API to get the concept URI for a given keyword. 
    This helps in searching events related to the keyword.
    """
    if not NEWS_API_KEY:
        raise ValueError("NEWS_API_KEY not found in the environment variables.")
    
    er = EventRegistry(apiKey=NEWS_API_KEY, allowUseOfArchive=False)
    concept_info = er.suggestConcepts(keyword, source="news")
    
    if concept_info:
        return concept_info[0].get("uri")  # Return the URI of the top suggestion
    else:
        print(f"No concept URI found for keyword '{keyword}'")
        return None


def main(keyword):
    """
    Main function to fetch both articles and events related to the input keyword.
    It returns two DataFrames: one for articles and one for events.
    """
    # Fetch articles related to the keyword
    articles_df = get_articles_by_keyword(keyword, max_items=100, save_to_csv=False, csv_filename=f'{keyword}.csv')

    # Get the concept URI for the keyword to fetch related events
    concept_uri = get_concept_uri(keyword)
    concept_uri = False    

    if concept_uri:
        events_df = get_events_by_concept(concept_uri, max_items=50, save_to_csv=False, csv_filename=f'{keyword}.csv')
    else:
        events_df = pd.DataFrame()  # Return empty DataFrame if no concept URI is found

    return articles_df, events_df


# Example usage:
if __name__ == "__main__":
    user_input = input("Enter a keyword (e.g., 'Google CEO', 'Bitcoin', 'Israel War'): ")
    articles_df, events_df = main(user_input)
    
    print("Articles DataFrame:")
    print(articles_df)

