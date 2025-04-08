from dotenv import load_dotenv
import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings, StorageContext, load_index_from_storage, ServiceContext
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
import openai
import logging
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set API key directly
os.environ["OPENAI_API_KEY"] = "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"

# Load environment variables (this will now use the key we just set)
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Configure global settings for OpenAI models
Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0)
Settings.embed_model = OpenAIEmbedding()

def create_index(content: bytes, persist_dir: str) -> None:
    """
    Create an index from PDF content and persist it to disk.
    
    Args:
        content: The PDF file content as bytes
        persist_dir: Directory to store the index
    """
    try:
        # Create a temporary file to store the PDF content
        temp_file = os.path.join(persist_dir, "temp.pdf")
        with open(temp_file, "wb") as f:
            f.write(content)
        
        # Create a custom node parser with larger chunks and more overlap
        node_parser = SentenceSplitter(
            chunk_size=1024,
            chunk_overlap=200,
            paragraph_separator="\n\n"
        )
        
        # Create service context with custom node parser
        service_context = ServiceContext.from_defaults(
            node_parser=node_parser,
            llm=OpenAI(temperature=0, model="gpt-3.5-turbo"),
            embed_model=OpenAIEmbedding()
        )
        
        # Create storage context
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        
        # Load documents and create index
        documents = SimpleDirectoryReader(input_files=[temp_file]).load_data()
        index = VectorStoreIndex.from_documents(
            documents,
            service_context=service_context,
            storage_context=storage_context
        )
        
        # Persist the index
        index.storage_context.persist(persist_dir=persist_dir)
        
        # Clean up temporary file
        os.remove(temp_file)
        
        logger.info("Index created and persisted successfully")
        
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise

def query_index(query_text: str, persist_dir: str) -> str:
    """
    Query the index with the given text.
    
    Args:
        query_text: The query text
        persist_dir: Directory where the index is stored
    
    Returns:
        The response text
    """
    try:
        # Load the index from storage
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        index = load_index_from_storage(storage_context)
        
        # Create query engine with custom settings
        query_engine = index.as_query_engine(
            similarity_top_k=8,
            response_mode="compact",
            text_qa_template=(
                "You are a helpful AI assistant. Answer the question based ONLY on the provided context. "
                "If the context doesn't contain the answer, say 'I don't have enough information to answer that question.' "
                "Context: {context_str}\n\nQuestion: {query_str}\n\nAnswer: "
            )
        )
        
        # Get response
        response = query_engine.query(query_text)
        return str(response)
        
    except Exception as e:
        logger.error(f"Error querying index: {str(e)}")
        raise

if __name__ == "__main__":
    pdf_dir = "pdfs"
    persist_dir = "storage"
    
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    # Check if we need to create a new index
    if not os.path.exists(persist_dir) or not os.path.exists(os.path.join(persist_dir, "docstore.json")):
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
            print(f"Please add your PDF documents to the {pdf_dir} directory")
            exit(1)
        print("Creating new index...")
        index = create_index(pdf_dir, persist_dir)
    else:
        print("Loading existing index...")
        index = load_index(persist_dir)
    
    while True:
        query = input("\nEnter your question (or 'quit' to exit): ")
        if query.lower() == 'quit':
            break
        
        print("\nProcessing query...")
        response = query_index(query, persist_dir)
        print(f"\nResponse: {response}") 