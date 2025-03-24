from flask import Flask, request, jsonify, send_file
import os
from utils import NewsExtractor, configure_dns

app = Flask(__name__)

# Initialize extractor with API key
extractor = None

@app.route('/api/init', methods=['POST'])
def initialize_extractor():
    global extractor
    data = request.json
    api_key = data.get('api_key')
    
    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    
    try:
        # Configure DNS before initializing
        configure_dns()
        extractor = NewsExtractor(api_key.strip())
        return jsonify({"status": "success", "message": "Extractor initialized successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_company():
    global extractor
    
    if not extractor:
        return jsonify({"error": "Extractor not initialized. Please provide API key first."}), 400
    
    data = request.json
    company_name = data.get('company_name')
    max_articles = data.get('max_articles', 10)
    
    if not company_name:
        return jsonify({"error": "Company name is required"}), 400
    
    try:
        # Set max timeout for the request to prevent long-running requests
        articles_data = extractor.extract_and_analyze(company_name, max_articles=max_articles)
        formatted_output = extractor.format_data_for_output(company_name, articles_data)
        
        return jsonify(formatted_output)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/translate', methods=['POST'])
def translate_text():
    global extractor
    
    if not extractor:
        return jsonify({"error": "Extractor not initialized. Please provide API key first."}), 400
    
    data = request.json
    text = data.get('text')
    
    if not text:
        return jsonify({"error": "Text is required for translation"}), 400
    
    try:
        hindi_text = extractor.translate_to_hindi(text)
        return jsonify({"translated_text": hindi_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate_speech', methods=['POST'])
def generate_speech():
    global extractor
    
    if not extractor:
        return jsonify({"error": "Extractor not initialized. Please provide API key first."}), 400
    
    data = request.json
    text = data.get('text')
    filename = data.get('filename', 'analysis_hindi.mp3')
    
    if not text:
        return jsonify({"error": "Text is required for speech generation"}), 400
    
    try:
        file_path, hindi_text = extractor.generate_hindi_speech(text, filename)
        if file_path:
            return jsonify({
                "success": True,
                "file_url": f"/static/{os.path.basename(file_path)}",
                "translated_text": hindi_text
            })
        else:
            return jsonify({"error": "Failed to generate speech"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_file(os.path.join('static', filename))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)