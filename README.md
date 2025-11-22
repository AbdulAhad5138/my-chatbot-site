# Gemini AI Workspace with Groq Integration

This is a powerful AI Chatbot that integrates multiple tools to provide comprehensive answers:
- **Google Gemini**: Main conversational engine.
- **Groq (Llama 3)**: Expert consultant for second opinions.
- **Wikipedia**: Knowledge base search.
- **DuckDuckGo**: Real-time web search.
- **arXiv**: Academic paper search.
- **PDF Analysis**: Upload and chat with PDF documents.

## Project Structure
- `frontend/`: Contains the HTML, CSS, and JavaScript for the user interface.
- `backend/`: Contains the Flask server (`app.py`) and dependencies.

## Setup & Running

1.  **Install Dependencies**:
    Open a terminal in the `backend` folder and run:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration**:
    - The application uses API keys for Gemini and Groq.
    - These are currently configured in `backend/app.py` or `backend/.env`.

3.  **Start the Backend**:
    ```bash
    cd backend
    python app.py
    ```
    The server will start at `http://localhost:5000`.

4.  **Launch the Frontend**:
    - Open the `frontend/index.html` file in any web browser.
    - Start chatting!

## Features
- **Smart Tool Selection**: The agent automatically decides which tools to use based on your query.
- **Parallel Execution**: Searches are run simultaneously for faster results.
- **Source Citations**: The bot lists exactly which sources were used for each answer.
