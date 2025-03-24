# 📰 Company News Analyzer

The **Company News Analyzer** is a Streamlit-based web app that extracts and analyzes recent news articles about a company. It leverages AI-powered analysis (Gemini API) to provide insights, summaries, key topics, sentiment analysis, and more! The app also translates the analysis into Hindi and generates speech from the Hindi translation.

## 🚀 Features

- ✅ Analyze the latest news articles about any company
- ✅ AI-powered analysis & summarization using Gemini API
- ✅ Sentiment analysis of news articles with interactive visualizations
- ✅ Identify frequently mentioned topics and sources
- ✅ Translate AI-generated insights into Hindi
- ✅ Generate speech from Hindi translations
- ✅ Download analysis results as JSON or CSV files
- ✅ Clean, interactive UI built with Streamlit and Plotly

## 🛠️ Tech Stack

* **Frontend:** Streamlit
* **Backend:** Flask
* **AI & NLP:** Gemini AI API
* **Visualization:** Plotly Express
* **Language Translation & TTS:** Gemini AI + Flask backend

## 📂 Project Structure

```
📦 Company News Analyzer
 ┣ 📜 app.py           # Streamlit frontend app
 ┣ 📜 README.md        # Project documentation (this file)
 ┣ 📜 requirements.txt # Python dependencies
 ┗ 🔧 Flask Backend    # Flask backend folder (separate)
```

## ⚙️ Setup Instructions

### Prerequisites
* Python 3.8+
* Gemini AI API Key
* Flask backend server (already developed and running on localhost:8000)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/company-news-analyzer.git
cd company-news-analyzer
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

For the backend (Flask), make sure it runs and listens on port `8000`. Ensure the API endpoints are functional:
* `/api/init`
* `/api/analyze`
* `/api/translate`
* `/api/generate_speech`

### 3. Run the Streamlit App

```bash
streamlit run app.py
```

The app will open automatically in your browser at: `http://localhost:8501`

## 📝 How to Use the App

1. **Enter your Gemini API Key** in the sidebar and click `Initialize API`.
2. Provide a **company name** (e.g., Apple, Tesla, Microsoft).
3. Select the **number of articles** to analyze (default is 10).
4. Click **Analyze News** to run the AI-powered analysis.
5. View the results in three tabs:
   * **English Analysis**
   * **Articles**
   * **Visualizations**
6. Translate the insights into **Hindi** and generate **speech** if needed.
7. Download the results in **JSON** or **CSV** format.

## 🖼️ App Preview

<!-- Add screenshots here when available -->

## 🔐 Gemini API Setup

1. Sign up and get your **Gemini AI API Key** from Google AI Studio.
2. Enter the API Key in the sidebar when you run the app.

## ⚡ Example API Endpoints (Flask backend)

| Endpoint | Description |
|----------|-------------|
| `/api/init` | Initialize Gemini API Key |
| `/api/analyze` | Analyze news articles |
| `/api/translate` | Translate text to Hindi |
| `/api/generate_speech` | Generate speech (MP3) |

## 🧑‍💻 Contributing

Pull requests are welcome! If you want to improve the app or add new features:

1. Fork the repo
2. Create your branch
```bash
git checkout -b feature/new-feature
```
3. Commit your changes
```bash
git commit -m 'Add new feature'
```
4. Push to the branch
```bash
git push origin feature/new-feature
```
5. Create a new Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙌 Acknowledgements

* Streamlit
* Plotly Express
* Google Gemini AI
* Flask

## 📬 Contact

If you have any questions or feedback:
📧 Email: your.email@example.com
🌐 GitHub: yourusername
