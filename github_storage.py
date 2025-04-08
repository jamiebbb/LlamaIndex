import os
import base64
import requests
import logging
from datetime import datetime
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GitHubStorage:
    def __init__(self, token, username, repo_name):
        self.token = token
        self.username = username
        self.repo_name = repo_name
        self.base_url = f"https://api.github.com/repos/{username}/{repo_name}"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Check if repository exists, create if not
        self._ensure_repo_exists()
        
    def _ensure_repo_exists(self):
        """Ensure the GitHub repository exists"""
        try:
            response = requests.get(self.base_url, headers=self.headers)
            
            if response.status_code == 404:
                # Repository doesn't exist, create it
                data = {
                    "name": self.repo_name,
                    "private": True,
                    "auto_init": True
                }
                
                response = requests.post(
                    f"https://api.github.com/user/repos",
                    headers=self.headers,
                    json=data
                )
                
                response.raise_for_status()
            
            # Create pdfs directory if it doesn't exist
            self._ensure_directory_exists("pdfs")
            
        except Exception as e:
            logger.error(f"Error ensuring repository exists: {str(e)}")
            raise
    
    def _ensure_directory_exists(self, path):
        """Ensure a directory exists in the repository"""
        try:
            # Check if directory exists
            response = requests.get(
                f"{self.base_url}/contents/{path}",
                headers=self.headers
            )
            
            if response.status_code == 404:
                # Directory doesn't exist, create it with a README
                readme_content = base64.b64encode(
                    f"# {path} Directory\nThis directory contains PDF files.".encode()
                ).decode()
                
                create_data = {
                    "message": f"Create {path} directory",
                    "content": readme_content
                }
                
                response = requests.put(
                    f"{self.base_url}/contents/{path}/README.md",
                    headers=self.headers,
                    json=create_data
                )
                
                if response.status_code in [201, 200]:
                    logger.info(f"Created directory: {path}")
                else:
                    logger.error(f"Failed to create directory: {response.text}")
                    
        except Exception as e:
            logger.error(f"Error ensuring directory exists: {str(e)}")
            raise
    
    def upload_file(self, filename, content):
        """Upload a file to GitHub."""
        try:
            self._ensure_repo_exists()
            
            # Encode file content
            content_b64 = base64.b64encode(content).decode('utf-8')
            
            # Prepare the file data
            data = {
                "message": f"Upload {filename}",
                "content": content_b64,
                "branch": "main"
            }
            
            # Check if file exists
            response = requests.get(
                f"{self.base_url}/contents/{filename}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                # File exists, update it
                file_data = response.json()
                data["sha"] = file_data["sha"]
                response = requests.put(
                    f"{self.base_url}/contents/{filename}",
                    headers=self.headers,
                    json=data
                )
            else:
                # File doesn't exist, create it
                response = requests.put(
                    f"{self.base_url}/contents/{filename}",
                    headers=self.headers,
                    json=data
                )
            
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Error uploading file to GitHub: {str(e)}")
            raise
    
    def get_file_url(self, filename):
        """Get the download URL for a file."""
        try:
            response = requests.get(
                f"{self.base_url}/contents/{filename}",
                headers=self.headers
            )
            response.raise_for_status()
            
            return response.json()["download_url"]
            
        except Exception as e:
            logger.error(f"Error getting file URL from GitHub: {str(e)}")
            raise
    
    def list_files(self):
        """List all files in the repository."""
        try:
            self._ensure_repo_exists()
            
            response = requests.get(
                f"{self.base_url}/contents",
                headers=self.headers
            )
            response.raise_for_status()
            
            files = []
            for item in response.json():
                if item["type"] == "file" and item["name"].endswith(".pdf"):
                    files.append({
                        "filename": item["name"],
                        "size": item["size"],
                        "url": item["download_url"],
                        "last_modified": item["updated_at"]
                    })
            
            return files
            
        except Exception as e:
            logger.error(f"Error listing files from GitHub: {str(e)}")
            raise
    
    def delete_file(self, key):
        """Delete a file from GitHub"""
        try:
            # First get the file's SHA
            response = requests.get(
                f"{self.base_url}/contents/{key}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get file SHA: {response.text}")
                return False
            
            sha = response.json()['sha']
            
            # Delete the file
            data = {
                "message": f"Delete {key}",
                "sha": sha
            }
            
            response = requests.delete(
                f"{self.base_url}/contents/{key}",
                headers={"Authorization": f"token {self.github_token}"},
                json=data
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Failed to delete file: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting file from GitHub: {str(e)}")
            raise 