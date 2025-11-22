
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import google.generativeai as genai
from werkzeug.utils import secure_filename
import PyPDF2
import wikipedia
from duckduckgo_search import DDGS
import arxiv
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini API
# Try to get key from environment variable, fallback to hardcoded (for now, but warn user)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyDhmy5OnMw73B-A2Tt4ztANNdKuR7rBzpE"

if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY not found. Please set it in a .env file.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash") # Updated to latest stable flash model if available, or stick to 1.5/pro

PDF_TEXT = ""  # Store extracted PDF text for context

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    global PDF_TEXT
    if 'pdf' not in request.files:
        return jsonify({'error': 'No PDF file uploaded.'}), 400
    file = request.files['pdf']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    filename = secure_filename(file.filename)
    try:
        reader = PyPDF2.PdfReader(file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        PDF_TEXT = text
        return jsonify({'message': 'PDF uploaded and text extracted successfully.'})
    except Exception as e:
        return jsonify({'error': f'Failed to process PDF: {str(e)}'}), 500

@app.route('/tool_search', methods=['POST'])
def tool_search():
    data = request.get_json()
    query = data.get('query', '')
    tool = data.get('tool', '')
    
    if not query or not tool:
        return jsonify({'result': 'Missing query or tool.'}), 400
        
    try:
        if tool == 'wikipedia':
            summary = wikipedia.summary(query, sentences=3)
            return jsonify({'result': summary})
        elif tool == 'duckduckgo':
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=1))
                answer = results[0]['body'] if results else 'No results found.'
            return jsonify({'result': answer})
        elif tool == 'arxiv':
            search = arxiv.Search(query=query, max_results=1)
            papers = list(search.results())
            if papers:
                paper = papers[0]
                info = f"Title: {paper.title}\nAuthors: {', '.join(a.name for a in paper.authors)}\nSummary: {paper.summary[:500]}..."
                return jsonify({'result': info})
            else:
                return jsonify({'result': 'No papers found.'})
        else:
            return jsonify({'result': 'Unknown tool.'}), 400
    except Exception as e:
        return jsonify({'result': f'Error: {str(e)}'}), 500


@app.route('/agent', methods=['POST'])
def agent():
    global PDF_TEXT
    data = request.get_json()
    user_message = data.get('message', '')
    query = data.get('query', '') or user_message
    
    if not user_message:
         return jsonify({'reply': 'Please enter a message.', 'agent_context': []}), 400

    context_parts = []
    
    # 1. PDF context (always check first if available)
    if PDF_TEXT:
        context_parts.append(f"PDF Context:\n{PDF_TEXT[:10000]}")

    # Helper functions for tools
    def search_wikipedia(q):
        try:
            return f"Wikipedia:\n{wikipedia.summary(q, sentences=2)}"
        except:
            return None

    def search_duckduckgo(q):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(q, max_results=2))
                if results:
                    return f"DuckDuckGo:\n" + "\n".join([r['body'] for r in results])
        except:
            return None

    def search_arxiv(q):
        try:
            search = arxiv.Search(query=q, max_results=1)
            papers = list(search.results())
            if papers:
                paper = papers[0]
                return f"arXiv:\nTitle: {paper.title}\nSummary: {paper.summary[:500]}..."
        except:
            return None

    def search_chatgpt(q):
        try:
            # Using the provided Groq API Key
            api_key = "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"
            
            # Configure OpenAI client for Groq
            client = openai.OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[
                    {"role": "system", "content": "You are a helpful expert consultant. Provide a concise, high-level summary or insight about the user's query to help another AI answer the question better."},
                    {"role": "user", "content": q}
                ],
                max_tokens=150
            )
            return f"ChatGPT (Groq):\n{response.choices[0].message.content}"
        except Exception as e:
            print(f"Groq Error: {e}") 
            return None

    # Run tools in parallel
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(search_wikipedia, query),
            executor.submit(search_duckduckgo, query),
            executor.submit(search_arxiv, query),
            executor.submit(search_chatgpt, query)
        ]
        
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                context_parts.append(result)

    # Compose prompt
    system_instruction = (
        "You are an advanced AI research assistant. Your goal is to provide the BEST possible answer "
        "by synthesizing information from multiple sources (PDF, Wikipedia, Web Search, Academic Papers, and ChatGPT Insights). "
        "Compare the information from different tools and construct a comprehensive, accurate, and well-cited response. "
        "If the context is not relevant, answer from your own knowledge but mention that external tools yielded no results."
    )
    prompt = f"{system_instruction}\n\nContext:\n" + '\n\n'.join(context_parts) + f"\n\nUser: {user_message}"
    
    try:
        response = model.generate_content(prompt)
        reply = response.text
        return jsonify({'reply': reply, 'agent_context': context_parts})
    except Exception as e:
        return jsonify({'reply': f'Error generating response: {str(e)}', 'agent_context': context_parts}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
