📰 Company News Analyzer
The Company News Analyzer is a Streamlit-based web app that extracts and analyzes recent news articles about a company. It leverages AI-powered analysis (Gemini API) to provide insights, summaries, key topics, sentiment analysis, and more! The app also translates the analysis into Hindi and generates speech from the Hindi translation.

🚀 Features
✅ Analyze the latest news articles about any company
✅ AI-powered analysis & summarization using Gemini API
✅ Sentiment analysis of news articles with interactive visualizations
✅ Identify frequently mentioned topics and sources
✅ Translate AI-generated insights into Hindi
✅ Generate speech from Hindi translations
✅ Download analysis results as JSON or CSV files
✅ Clean, interactive UI built with Streamlit and Plotly

🛠️ Tech Stack
Frontend: Streamlit

Backend: Flask (runs separately)

AI & NLP: Gemini AI API

Visualization: Plotly Express

Language Translation & TTS: Gemini AI + Flask backend

📂 Project Structure
bash
Copy
Edit
📦 Company News Analyzer
 ┣ 📜 app.py                # Streamlit frontend app
 ┣ 📜 README.md             # Project documentation (this file)
 ┣ 📜 requirements.txt      # Python dependencies
 ┗ 🔧 Flask Backend         # Flask backend folder (separate)
⚙️ Setup Instructions
Prerequisites
Python 3.8+

Gemini AI API Key

Flask backend server (already developed and running on localhost:8000)

1. Clone the Repository
bash
Copy
Edit
git clone https://github.com/yourusername/company-news-analyzer.git
cd company-news-analyzer
2. Install Dependencies
bash
Copy
Edit
pip install -r requirements.txt
For the backend (Flask), make sure it runs and listens on port 8000.
Ensure the API endpoints are functional:

/api/init

/api/analyze

/api/translate

/api/generate_speech

3. Run the Streamlit App
bash
Copy
Edit
streamlit run app.py
The app will open automatically in your browser at:
http://localhost:8501

📝 How to Use the App
Enter your Gemini API Key in the sidebar and click Initialize API.

Provide a company name (e.g., Apple, Tesla, Microsoft).

Select the number of articles to analyze (default is 10).

Click Analyze News to run the AI-powered analysis.

View the results in three tabs:

English Analysis

Articles

Visualizations

Translate the insights into Hindi and generate speech if needed.

Download the results in JSON or CSV format.
