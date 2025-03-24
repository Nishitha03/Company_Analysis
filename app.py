import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import base64

# Set page configuration
st.set_page_config(
    page_title="Company News Analyzer",
    page_icon="📰",
    layout="wide"
)

# Constants
API_BASE_URL = "http://localhost:8000/api"  # Change this if your Flask app runs on a different port

# Function to get base64 encoding of an audio file
def get_audio_base64(file_url):
    try:
        audio_response = requests.get(f"http://localhost:8000{file_url}", timeout=10)
        if audio_response.status_code == 200:
            audio_bytes = audio_response.content
            audio_b64 = base64.b64encode(audio_bytes).decode()
            return audio_b64
        else:
            st.error(f"Error fetching audio file: {audio_response.status_code}")
            return None
    except Exception as e:
        st.error(f"Error processing audio: {str(e)}")
        return None

# App title and description
st.title("📰 Company News Analyzer")
st.markdown("""
This app extracts and analyzes recent news articles about a company.
It provides summaries, identifies key topics, and generates insights about the news coverage.
It can also translate analysis to Hindi and generate speech.
""")

# Initialize session state variables
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
if 'api_key_validated' not in st.session_state:
    st.session_state.api_key_validated = False
if 'hindi_translation' not in st.session_state:
    st.session_state.hindi_translation = None
if 'speech_file_url' not in st.session_state:
    st.session_state.speech_file_url = None

# API Key setup in sidebar
with st.sidebar:
    st.header("Setup")
    api_key = st.text_input("Enter your Gemini API Key", type="password")
    
    if st.button("Initialize API", key="init_api_button"):
        if not api_key:
            st.error("Please enter an API key")
        else:
            try:
                response = requests.post(
                    f"{API_BASE_URL}/init",
                    json={"api_key": api_key},
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.session_state.api_key_validated = True
                    st.session_state.initialized = True
                    st.success("API initialized successfully!")
                else:
                    st.error(f"Error: {response.json().get('error', 'Unknown error')}")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")
                st.info("Make sure your Flask backend is running at " + API_BASE_URL)

# Main content
if st.session_state.api_key_validated:
    # Input section
    st.header("Analyze Company News")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        company_name = st.text_input("Company Name", placeholder="e.g., Apple, Microsoft, Tesla")
    
    with col2:
        max_articles = st.slider("Maximum Articles", min_value=3, max_value=20, value=10)
    
    # Analyze button
    if st.button("Analyze News", key="analyze_button", disabled=not company_name):
        with st.spinner(f"Analyzing news for {company_name}... This may take a few minutes."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/analyze",
                    json={"company_name": company_name, "max_articles": max_articles},
                    timeout=300  # 5 minute timeout
                )
                
                if response.status_code == 200:
                    st.session_state.analysis_results = response.json()
                    # Reset translation and speech when new analysis is done
                    st.session_state.hindi_translation = None
                    st.session_state.speech_file_url = None
                    st.success("Analysis complete!")
                else:
                    st.error(f"Error: {response.json().get('error', 'Unknown error')}")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")
    
    # Display results if available
    if st.session_state.analysis_results:
        results = st.session_state.analysis_results
        
        # Company and general info
        st.header(f"Analysis Results for {results['Company']}")
        
        # Create tabs for English, Articles, and Visualizations (removed Hindi tab)
        analysis_tabs = st.tabs(["English Analysis", "Articles", "Visualizations"])
        
        with analysis_tabs[0]:
            # LLM Analysis
            st.subheader("AI Analysis")
            st.info(results["LLM Analysis"])
            
            # Sentiment Score Visualization
            if "Articles" in results and isinstance(results["Articles"], list) and len(results["Articles"]) > 0:
                st.subheader("Sentiment Analysis")
                
                # Extract sentiment scores from articles
                sentiment_data = []
                for i, article in enumerate(results["Articles"]):
                    if "sentiment_score" in article and "Title" in article:
                        # Use shortened title for better display
                        title = article["Title"]
                        if len(title) > 50:
                            title = title[:47] + "..."
                        
                        sentiment_data.append({
                            "Article": f"Article {i+1}",
                            "Title": title,
                            "Sentiment Score": float(article["sentiment_score"]),
                            "Sentiment": article.get("sentiment", "neutral")
                        })
                
                if sentiment_data:
                    # Create DataFrame for visualization
                    sentiment_df = pd.DataFrame(sentiment_data)
                    
                    # Create horizontal bar chart for sentiment scores
                    fig = px.bar(
                        sentiment_df,
                        y="Article",
                        x="Sentiment Score",
                        orientation="h",
                        title="Sentiment Scores Across Articles",
                        labels={"Sentiment Score": "Score (-1 to 1)", "Article": ""},
                        color="Sentiment Score",
                        color_continuous_scale="RdBu",
                        hover_data=["Title", "Sentiment"],
                        range_x=[-1, 1]  # Fixed scale from -1 to 1
                    )
                    
                    # Add a vertical line at x=0 to show neutral point
                    fig.add_vline(x=0, line_dash="dash", line_color="gray")
                    
                    # Customize layout
                    fig.update_layout(
                        xaxis_title="Negative ← Neutral → Positive",
                        yaxis=dict(autorange="reversed")  # To show articles in the original order
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Add average sentiment score
                    if len(sentiment_df) > 0:
                        avg_score = sentiment_df["Sentiment Score"].mean()
                        st.metric(
                            label="Average Sentiment Score", 
                            value=f"{avg_score:.2f}",
                            delta=f"{'Positive' if avg_score > 0 else 'Negative' if avg_score < 0 else 'Neutral'}"
                        )
                else:
                    st.warning("No sentiment scores available for visualization.")
            
            # Hindi translation section (now directly in the English tab)
            st.subheader("Hindi Translation")
            
            # Button to translate
            if st.button("Translate to Hindi", key="translate_button"):
                with st.spinner("Translating analysis to Hindi..."):
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/translate",
                            json={"text": results["LLM Analysis"]},
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            st.session_state.hindi_translation = response.json()["translated_text"]
                            st.success("Translation complete!")
                        else:
                            st.error(f"Error fetching translation: {response.json().get('error', 'Unknown error')}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Connection error: {str(e)}")
            
            # Display Hindi translation if available (directly below the button)
            if st.session_state.hindi_translation:
                st.info(st.session_state.hindi_translation)
                
                # Button to generate speech
                if st.button("Generate Speech", key="speech_button"):
                    with st.spinner("Generating speech from Hindi translation..."):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/generate_speech",
                                json={"text": st.session_state.hindi_translation},
                                timeout=60
                            )
                            
                            if response.status_code == 200:
                                st.session_state.speech_file_url = response.json()["file_url"]
                                st.success("Speech generated successfully!")
                            else:
                                st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Connection error: {str(e)}")
                
                # Display audio player if speech file is available
                if st.session_state.speech_file_url:
                    audio_b64 = get_audio_base64(st.session_state.speech_file_url)
                    if audio_b64:
                        st.audio(f"data:audio/mp3;base64,{audio_b64}", format="audio/mp3")
                    else:
                        st.error("Error loading audio file")
            
            # Download results
            if st.download_button(
                label="Download Analysis as JSON",
                data=json.dumps(results, indent=4),
                file_name=f"{results['Company'].replace(' ', '_')}_news_analysis.json",
                mime="application/json",
                key="download_json_button"
            ):
                st.success("Download complete!")
        
        with analysis_tabs[1]:
            # Articles tab view
            st.subheader("Articles")
            if "Articles" in results:
                # Check if Articles is a list of dictionary format (second example) or dataframe format (first example)
                if isinstance(results["Articles"], list) and len(results["Articles"]) > 0 and isinstance(results["Articles"][0], dict):
                    # Create tabs for each article
                    article_tabs = st.tabs([f"Article {i+1}" for i in range(len(results["Articles"]))])
                    
                    for i, (tab, article) in enumerate(zip(article_tabs, results["Articles"])):
                        with tab:
                            # Check if article has the expected keys (second example format)
                            if "Title" in article and "URL" in article:
                                st.markdown(f"### [{article['Title']}]({article['URL']})")
                                if "sentiment" in article:
                                    st.markdown(f"**Sentiment:** {article['sentiment']}")
                                if "sentiment_score" in article:
                                    st.markdown(f"**Sentiment Score:** {article['sentiment_score']}")
                                st.markdown("**Summary:**")
                                if "Summary" in article:
                                    st.write(article['Summary'])
                                st.markdown("**Topics:**")
                                if "Topics" in article and isinstance(article['Topics'], list):
                                    st.write(", ".join(article['Topics']))
                                    
                                # Add button to open article in new tab
                                st.markdown(f"[Read Full Article]({article['URL']})")
                            else:
                                # Fallback to display whatever keys the article has
                                for key, value in article.items():
                                    st.markdown(f"**{key}:** {value}")
                else:
                    # Handle dataframe-like structure (first example)
                    articles_df = pd.DataFrame(results["Articles"])
                    st.dataframe(articles_df)
                    
                    # Download link for articles data
                    csv = articles_df.to_csv(index=False)
                    st.download_button(
                        label="Download Articles Data",
                        data=csv,
                        file_name=f"{results['Company']}_news_articles.csv",
                        mime="text/csv",
                        key="download_csv_button"
                    )
            else:
                st.warning("No articles found for this company.")
        
        with analysis_tabs[2]:
            st.subheader("Data Visualizations")
            
            # Sentiment Analysis
            if "sentiment" in results:
                st.subheader("Sentiment Analysis")
                
                sentiment_data = results["Sentiment"]
                
                # Create sentiment pie chart
                fig = px.pie(
                    names=list(sentiment_data.keys()),
                    values=list(sentiment_data.values()),
                    title="News Sentiment Distribution",
                    color_discrete_sequence=px.colors.sequential.RdBu,
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Topics Analysis
            if "Comparison" in results:
                st.subheader("Key Topics")
                
                topics_data = results["Comparison"]['topics']['shared']
                
                # Create horizontal bar chart for topics
                if isinstance(topics_data, dict):
                    topic_df = pd.DataFrame({"Topic": list(topics_data.keys()), "Count": list(topics_data.values())})
                    topic_df = topic_df.sort_values("Count", ascending=True)
                    
                    fig = px.bar(
                        topic_df,
                        x="Count",
                        y="Topic",
                        orientation="h",
                        title="Frequently Mentioned Topics",
                        color="Count",
                        color_continuous_scale=px.colors.sequential.Viridis
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Handle case where Topics is a list
                    st.write("Top Topics:")
                    for topic in topics_data:
                        st.markdown(f"- {topic}")
                        
            # Sources Analysis
            if "Sources" in results:
                st.subheader("News Sources")
                
                sources_data = results["Sources"]
                
                # Create source count chart
                if isinstance(sources_data, dict):
                    source_df = pd.DataFrame({"Source": list(sources_data.keys()), "Count": list(sources_data.values())})
                    source_df = source_df.sort_values("Count", ascending=False)
                    
                    fig = px.bar(
                        source_df,
                        x="Source",
                        y="Count",
                        title="Article Sources",
                        color="Count",
                        color_continuous_scale=px.colors.sequential.Blues
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Handle case where Sources is a list
                    st.write("News Sources:")
                    for source in sources_data:
                        st.markdown(f"- {source}")
                    
else:
    # Show instructions if API key not yet validated
    st.info("Please enter your Gemini API Key in the sidebar and click 'Initialize API' to begin.")
    
    # Placeholder for demo image
    st.image("https://via.placeholder.com/800x400?text=Company+News+Analyzer+Demo", use_column_width=True)
    
    st.markdown("""
    ## How to use this app:
    
    1. Enter your Gemini API Key in the sidebar
    2. Click "Initialize API" to connect to the backend
    3. Enter a company name to analyze
    4. Adjust the number of articles to analyze if needed
    5. Click "Analyze News" to start the analysis
    6. View the results in the tabs below
    7. Translate to Hindi and generate speech if desired
    
    The app will retrieve recent news articles about the specified company and provide AI-powered analysis of the content.
    """)

# Footer
st.markdown("---")
st.markdown("📊 Company News Analyzer | Created with Streamlit, Flask, and Gemini AI")