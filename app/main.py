import os
import uuid
import json
import logging
from typing import List

from fastapi import FastAPI, UploadFile, File, HTTPException
import pdfplumber
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from dotenv import load_dotenv

# Import Pydantic models for structured data
from .models import ExtractedChunk, ContentMetadata, VectorizeResponse

# Load environment variables
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with a response model reference
app = FastAPI(title="PDF Vectorizer Service")

# --- Configuration ---
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "pdf_collection")

# --- Clients ---
# Initialize Qdrant Client
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Initialize Embedding Model (AvalAI/OpenAI)
# *** THIS LINE IS NOW CORRECTED ***
embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small", 
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    # Use the custom base URL if defined in .env
    openai_api_base=os.getenv("OPENAI_API_BASE", None), 
)

# --- Qdrant Setup ---
def init_qdrant():
    """Ensure the collection exists on startup."""
    try:
        collections = qdrant_client.get_collections()
        exists = any(c.name == COLLECTION_NAME for c in collections.collections)
        
        if not exists:
            # Vector size for text-embedding-3-small is 1536
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")

@app.on_event("startup")
async def startup_event():
    init_qdrant()

# --- Helper Functions ---

def extract_content_from_pdf(file_path: str) -> List[ExtractedChunk]:
    """
    Parses PDF to extract Text and Tables while preserving page context.
    Returns a list of ExtractedChunk Pydantic models.
    """
    extracted_chunks: List[ExtractedChunk] = []
    
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            
            # 1. Extract Tables
            tables = page.extract_tables()
            for table in tables:
                # Store table content as a JSON string
                # We use ensure_ascii=False to correctly handle Persian/UTF-8 characters
                table_content = json.dumps(table, ensure_ascii=False)
                metadata = ContentMetadata(page=page_num, section="Table Data")
                
                extracted_chunks.append(ExtractedChunk(
                    content_type="table",
                    text=table_content,
                    metadata=metadata
                ))

            # 2. Extract Text (Recursive Character Splitting for contextual chunks)
            text = page.extract_text()
            if text:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=1000, 
                    chunk_overlap=100,
                    separators=["\n\n", "\n", " ", ""] # Optimal separators for text flow
                )
                chunks = splitter.split_text(text)
                
                for chunk in chunks:
                    metadata = ContentMetadata(page=page_num, section="Text Content")
                    extracted_chunks.append(ExtractedChunk(
                        content_type="text",
                        text=chunk,
                        metadata=metadata
                    ))
            
            # 3. Image Placeholder 
            if page.images:
                # Use a counter for images on the same page
                for idx, img in enumerate(page.images):
                    metadata = ContentMetadata(
                        page=page_num, 
                        section="Image Placeholder",
                        related_images=[f"img_{page_num}_{idx}"]
                    )
                    extracted_chunks.append(ExtractedChunk(
                        content_type="image",
                        text=f"Placeholder for image {idx+1} detected on page {page_num}",
                        metadata=metadata
                    ))

    return extracted_chunks

# --- API Endpoint ---

@app.post("/vectorize", response_model=VectorizeResponse)
async def vectorize_pdf(file: UploadFile = File(...)):
    """
    Endpoint to process PDF, embed content, and store in Qdrant.
    The response structure is validated by the VectorizeResponse model.
    """
    file_location = f"/tmp/temp_{file.filename}"
    try:
        # 1. Save uploaded file temporarily
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
        
        # 2. Parse PDF and chunk
        chunks: List[ExtractedChunk] = extract_content_from_pdf(file_location)
        
        points = []
        
        # 3. Generate Embeddings & Prepare for Qdrant
        # Extract all text for batch embedding (more efficient)
        texts = [chunk.text for chunk in chunks]
        vectors = embedding_model.embed_documents(texts)
        
        for i, vector in enumerate(vectors):
            chunk = chunks[i]
            
            # Convert Pydantic model to a standard dict for the Qdrant payload
            payload = chunk.model_dump()
            
            points.append(PointStruct(
                id=str(uuid.uuid4()), 
                vector=vector,        
                payload=payload       
            ))

        # 4. Upsert to Qdrant
        if points:
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points,
                wait=True
            )

        return VectorizeResponse(
            status="success", 
            message=f"Successfully processed {len(points)} content chunks and upserted them to Qdrant.",
            filename=file.filename,
            chunks_processed=len(points)
        )

    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        # Raise an HTTPException to ensure a proper error response is returned
        raise HTTPException(
            status_code=500, 
            detail=f"An internal error occurred during vectorization: {str(e)}"
        )
    finally:
        # Cleanup
        if os.path.exists(file_location):
            os.remove(file_location)