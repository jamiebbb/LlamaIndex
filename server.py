import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from pdf_qa import create_index, query_index
from github import Github

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# GitHub configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
GITHUB_REPO = os.getenv('GITHUB_REPO')

# Initialize GitHub client
g = Github(GITHUB_TOKEN)
repo = g.get_user(GITHUB_USERNAME).get_repo(GITHUB_REPO)

# Storage configuration
STORAGE_DIR = "storage"
PDF_DATABASE_FILE = "pdf_database.json"

# Create storage directory if it doesn't exist
os.makedirs(STORAGE_DIR, exist_ok=True)

def load_pdf_database():
    """Load the PDF database from GitHub."""
    try:
        contents = repo.get_contents(PDF_DATABASE_FILE)
        return json.loads(contents.decoded_content.decode())
    except:
        return {}

def save_pdf_database(database):
    """Save the PDF database to GitHub."""
    try:
        contents = repo.get_contents(PDF_DATABASE_FILE)
        repo.update_file(
            PDF_DATABASE_FILE,
            "Update PDF database",
            json.dumps(database, indent=2),
            contents.sha
        )
    except:
        repo.create_file(
            PDF_DATABASE_FILE,
            "Create PDF database",
            json.dumps(database, indent=2)
        )

@app.route('/api/pdfs', methods=['GET'])
def list_pdfs():
    """List all PDFs in the database."""
    try:
        database = load_pdf_database()
        return jsonify(list(database.values()))
    except Exception as e:
        logger.error(f"Error listing PDFs: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/pdfs/<filename>', methods=['GET'])
def get_pdf(filename):
    """Get a specific PDF from GitHub."""
    try:
        contents = repo.get_contents(f"pdfs/{filename}")
        return send_file(
            contents.decoded_content,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"Error getting PDF: {str(e)}")
        return jsonify({"error": str(e)}), 404

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Upload a PDF file to GitHub and create its index."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        if not file.filename.endswith('.pdf'):
            return jsonify({"error": "File must be a PDF"}), 400
        
        filename = secure_filename(file.filename)
        content = file.read()
        
        # Upload PDF to GitHub
        try:
            repo.create_file(
                f"pdfs/{filename}",
                f"Upload {filename}",
                content
            )
        except:
            contents = repo.get_contents(f"pdfs/{filename}")
            repo.update_file(
                f"pdfs/{filename}",
                f"Update {filename}",
                content,
                contents.sha
            )
        
        # Create index for the PDF
        persist_dir = os.path.join(STORAGE_DIR, filename)
        os.makedirs(persist_dir, exist_ok=True)
        create_index(content, persist_dir)
        
        # Update PDF database
        database = load_pdf_database()
        database[filename] = {
            "filename": filename,
            "upload_date": datetime.now().isoformat(),
            "size": len(content)
        }
        save_pdf_database(database)
        
        return jsonify({"message": "File uploaded successfully"})
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/query', methods=['POST'])
def query():
    """Query the PDF index."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({"error": "No query provided"}), 400
        
        query_text = data['query']
        filename = data.get('filename')
        
        if not filename:
            return jsonify({"error": "No filename provided"}), 400
        
        persist_dir = os.path.join(STORAGE_DIR, filename)
        if not os.path.exists(persist_dir):
            return jsonify({"error": "PDF not indexed"}), 404
        
        response = query_index(query_text, persist_dir)
        return jsonify({"response": response})
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000) 