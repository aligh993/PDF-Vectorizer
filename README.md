

# **PDF Content Vectorization Microservice**

## **📄 Project Overview**

This project implements a highly modular and containerized microservice built with **FastAPI** designed to process PDF documents, extract structured content (text, tables, images), convert the content into high-quality semantic vector embeddings, and store them in a **Qdrant** vector database.

The solution is specifically engineered to handle multilingual documents, focusing on **Persian (Farsi) language** support, and ensures contextual integrity by preserving the relationships between different content types and pages.

### **🎯 Key Features**

* **FastAPI Backend:** Provides a high-performance, single endpoint for PDF processing.  
* **Robust PDF Parsing:** Utilizes `pdfplumber` for reliable extraction of text and tables.  
* **Context Preservation:** Employs recursive text splitting and payload metadata (page number, content type) to maintain semantic and positional relationships.  
* **Multilingual Support (Persian):** Fully supports UTF-8 encoding for correct parsing and embedding of Persian text content.  
* **AvalAI Integration:** Uses `LangChain` with `OpenAIEmbeddings` compatible with the AvalAI endpoint.  
* **Qdrant Storage:** Stores vector embeddings and comprehensive metadata for efficient semantic search and retrieval.  
* **Full Dockerization:** Easily deployable via `docker-compose`.

---

## **🏗️ System Architecture and Component Overview**

The entire system is orchestrated using Docker Compose, consisting of two main services:

| Component | Technology | Role |
| :---- | :---- | :---- |
| **App Service** | FastAPI, Python 3.9+ | Serves the main `/vectorize` API endpoint. Handles file uploads, PDF parsing, chunking, and calling the embedding model. |
| **Embedding Generation** | LangChain, `OpenAIEmbeddings` | Connects to the AvalAI endpoint using the provided API key to transform text chunks into vectors (default size 1536). |
| **Vector Database** | Qdrant | Stores the resulting vector embeddings and their associated structured metadata (payload). |

Code snippet
```Plaintext
ggraph TD
    A[User Uploads PDF] --> B{FastAPI /vectorize};
    B --> C(pdfplumber: Parse PDF);
    C --> D{Recursive Chunking & Metadata};
    D --> E(LangChain/OpenAIEmbeddings - AvalAI);
    E --> F[Vector Embeddings];
    F & D --> G(Qdrant Client: Upsert Points);
    G --> H[Qdrant Vector DB];
```
---

## **⚙️ Setup and Execution Guide**

### **Prerequisites**

1. **Docker:** Required to run the containerized application and Qdrant instance.  
2. **Docker Compose:** Required for multi-container orchestration.

### **1\. Repository Structure**

Ensure your project files are structured as follows:

```Plaintext
pdf-vectorizer/
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI entry point & Logic
│   └── models.py          # Pydantic models
├── Dockerfile             # Python environment setup
├── docker-compose.yml     # Orchestration of App + Qdrant
├── test_api.py            # Test the /vectorize endpoint
├── verify_qdrant.py       # Query Qdrant (retrieve the vectors)
├── requirements.txt       # Dependencies
├── .env                   # API Keys and Config
└── README.md
```

### **2\. Configuration (`.env` file)**

Create a file named `.env` in the root directory and populate it with your specific API key and configuration settings.

| Variable | Description | Value Example |
| :---- | :---- | :---- |
| OPENAI\_API\_KEY | AvalAI API Key | aa-Gq5r6H...1QNzOfM |
| OPENAI\_API\_BASE | Optional: Custom URL for the AvalAI API endpoint. Leave blank or comment out if using standard OpenAI API structure. | https://api.avalai.ir/v1 |
| QDRANT\_HOST | Hostname for the Qdrant service (must match docker-compose.yml). | qdrant |
| COLLECTION\_NAME | The name of the collection in Qdrant to use. | pdf\_collection |

### **3\. Build and Run**

Navigate to the project's root directory (`pdf-vectorizer/`) and run the following command to build the services and start the containers:

```Bash
docker-compose up --build
```

The service will be accessible at `http://localhost:8000`.

---

## **🚀 API Usage**

The microservice exposes a single endpoint for processing.

### **Endpoint**

`POST /vectorize`

**Content-Type:** `multipart/form-data`

**Parameter:**

* `file` (type: `file`): The PDF document to be processed.

### **Example Request (using `curl`)**

Ensure you replace `/path/to/your/document.pdf` with the actual path to your file.

```Bash
curl -X 'POST' \
  'http://localhost:8000/vectorize' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@/path/to/your/document.pdf'
```

### **Example Success Response**

```JSON
{
  "status": "success",
  "message": "Processed 15 chunks. Total points upserted to Qdrant.",
  "filename": "Technical Assignment Document.pdf"
}
```

---

## **✅ Verification Steps**

After running the API request, you can verify the data is correctly stored in Qdrant by running the verification script (assuming you installed `qdrant-client` locally):

```Bash
python verify_qdrant.py
```

This script connects directly to the Qdrant service running in Docker and lists a sample of the stored points, including the original Persian/English text content and the metadata (page, content type).

### **Qdrant Payload Structure**

Each point stored in Qdrant has a vector (the embedding) and a payload that contains the original data and metadata:

```JSON
{
  "id": "78a9c2d1-e3f4-4b5c-a678-1234567890ab",
  "vector": [0.123, -0.456, ...], // 1536-dimensional vector
  "payload": {
    "content_type": "text",
    "text": "این متن فارسی نمونه‌ای از محتوای استخراج شده از صفحه اول است.",
    "metadata": {
      "page": 1,
      "section": "Text Content"
    }
  }
}  
```

