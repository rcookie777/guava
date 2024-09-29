import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from eventregistry import *
from dotenv import load_dotenv
from newsapi_ai import get_articles_by_keyword
# Streamlit interface
st.title("News Sentiment Analysis")

# User input for keyword
keyword = st.text_input("Enter a keyword to search for articles (e.g., 'Google CEO', 'Bitcoin', 'Israel War'):")

if keyword:
    # Fetch articles for the given keyword
    df_articles = get_articles_by_keyword(keyword, max_items=50)

    # Display the articles DataFrame in Streamlit
    st.write(f"Articles related to '{keyword}'")
    st.write(df_articles)

    # Convert 'Published On' to datetime and 'Sentiment Score' to numeric
    df_articles['Published On'] = pd.to_datetime(df_articles['Published On'])
    df_articles['Sentiment Score'] = pd.to_numeric(df_articles['Sentiment Score'], errors='coerce')

    # Filter out rows with missing sentiment scores
    df_articles = df_articles.dropna(subset=['Sentiment Score'])

    # Extract dates and sentiments for plotting
    sent_dates = df_articles['Published On'].tolist()
    sentiments = df_articles['Sentiment Score'].tolist()

    # Create Plotly figure
    fig = go.Figure()

    # Add sentiment score line
    fig.add_trace(go.Scatter(x=sent_dates, y=sentiments, mode='lines', name='Sentiment Score'))

    # Update layout
    fig.update_layout(
        title=f'Sentiment Score over Time for "{keyword}"',
        xaxis_title='Date',
        yaxis_title='Sentiment Score',
        legend_title='Legend'
    )

    # Update hover data
    fig.update_traces(
        hovertemplate='<b>Date</b>: %{x}<br><b>Score</b>: %{y}<extra></extra>'
    )

    # Display plot in Streamlit
    st.plotly_chart(fig)