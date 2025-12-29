
import os
import glob
from google import genai
from google.genai import types

class KnowledgeLoader:
    """
    Handles uploading of Hive Knowledge (Markdown files) to Gemini's Native File API.
    This enables 'File Search' (RAG) capabilities for the agents.
    """
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
             self.api_key = os.environ.get("GOOGLE_API_KEY")
             
        if not self.api_key:
            raise ValueError("API Key not found.")
            
        self.client = genai.Client(api_key=self.api_key)
        
    def upload_knowledge_base(self, knowledge_dir: str = "knowledge"):
        """
        Uploads all valid text files from the directory to Gemini.
        Returns a list of file URIs.
        """
        uploaded_files = []
        
        # Find all .md files (recursively or flat)
        # For now, let's assume flat or specific key files
        files = glob.glob(os.path.join(knowledge_dir, "*.md"))
        
        print(f"Found {len(files)} documents in {knowledge_dir}")
        
        for file_path in files:
            print(f"Uploading {file_path}...")
            try:
                # Upload file
                # The SDK automatically handles mime_type inference usually, or we specify text/plain
                file_ref = self.client.files.upload(path=file_path)
                
                print(f" > Uploaded: {file_ref.name} (URI: {file_ref.uri})")
                uploaded_files.append(file_ref)
                
            except Exception as e:
                print(f"Failed to upload {file_path}: {e}")
                
        return uploaded_files
        
    def create_search_tool(self, file_uris):
        """
        Returns the tool configuration to enable File Search on these files.
        Note: In "Generative" models (Gemini 1.5), we pass these URIs in the request 'contents' 
        for caching, or use the 'retrieval' tool if using the Semantic Retriever API.
        
        For "Gemini 1.5 Pro" large context, we usually just pass the handles.
        """
        # For simple Context Caching (files < 32k tokens), we just return the objects/URIs
        # to be included in the chat history. 
        pass 

if __name__ == "__main__":
    # Example Usage
    loader = KnowledgeLoader()
    # Assuming run from root
    loader.upload_knowledge_base("knowledge")
