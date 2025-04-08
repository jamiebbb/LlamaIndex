# PDF QA System

A web application that allows users to upload PDF documents and ask questions about their content using AI. Built with Python (Flask) for the backend and a simple HTML/CSS/JS frontend.

## Features

- Upload and manage PDF documents
- Ask questions about PDF content using AI
- View all uploaded PDFs in a library
- Modern, responsive UI
- Persistent storage of PDFs and index

## Project Structure

```
pdf-qa-system/
├── server.py           # Flask server
├── pdf_qa.py           # Core PDF processing functionality
├── index.html          # Frontend interface
├── requirements.txt    # Python dependencies
├── .env                # Environment variables (API keys)
├── uploads/            # Directory for uploaded PDFs
├── storage/            # Directory for the index
└── pdf_database.json   # Database of uploaded PDFs
```

## Setup

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```
4. Run the server:
   ```
   python server.py
   ```
5. Access the application at http://localhost:8000

## Usage

1. **Upload PDFs**: Click the "Choose PDF" button to upload a PDF document
2. **Ask Questions**: Type your question in the chat interface and press Enter
3. **View PDFs**: Switch to the "PDF Library" tab to see all uploaded PDFs
4. **Rebuild Index**: If needed, click the "Rebuild Index" button to refresh the index

## Technologies Used

- **Backend**: Python, Flask, LlamaIndex
- **Frontend**: HTML, CSS, JavaScript, Tailwind CSS
- **AI**: OpenAI API (GPT-4o-mini)

## Notes

- The system uses OpenAI's API for embeddings and query processing
- PDFs are stored permanently in the `uploads` directory
- The index is stored in the `storage` directory for faster querying
- The system automatically rebuilds the index when new PDFs are uploaded

## License

MIT 