from pydantic import BaseModel, Field
from typing import Optional, List

# --- Core Data Models ---

class ContentMetadata(BaseModel):
    """Metadata associated with an extracted content chunk."""
    page: int = Field(..., description="The page number where the content was extracted.")
    section: str = Field(..., description="A description of the content section (e.g., 'Text Content', 'Table Data').")
    
    # Optional fields for future complex metadata (e.g., image tags, table structure)
    related_images: Optional[List[str]] = Field(None, description="List of internal IDs for related images, if content type is 'text'.")

class ExtractedChunk(BaseModel):
    """Represents a single piece of content extracted from the PDF before embedding."""
    content_type: str = Field(..., description="Type of content: 'text', 'table', or 'image'.")
    text: str = Field(..., description="The cleaned, chunked text content or JSON string of a table/image placeholder.")
    metadata: ContentMetadata = Field(..., description="Positional and sectional metadata.")

# --- API Response Model ---

class VectorizeResponse(BaseModel):
    """The structured response model for the /vectorize endpoint."""
    status: str = Field(..., description="Status of the operation, e.g., 'success' or 'error'.")
    message: str = Field(..., description="A human-readable message about the result.")
    filename: str = Field(..., description="The name of the processed PDF file.")
    chunks_processed: int = Field(..., description="The total number of chunks successfully processed and upserted.")