from qdrant_client import QdrantClient
import os

# Configuration
# These must match the values in your docker-compose and .env
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
# Default to 'pdf_collection' as defined in your .env, or 'pdf_docs' if using default fallback
COLLECTION_NAME = "pdf_collection" 

def verify_data():
    """
    Connects to Qdrant, checks for the collection, and retrieves sample data.
    """
    print(f"🔌 Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    
    try:
        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        
        # 1. Check Collection Status & Count
        # This confirms the collection exists and tells us how many chunks were stored
        collection_info = client.get_collection(collection_name=COLLECTION_NAME)
        print(f"✅ Collection '{COLLECTION_NAME}' found.")
        print(f"📊 Total Vectors Stored: {collection_info.points_count}")
        print(f"🟢 Status: {collection_info.status}")

        if collection_info.points_count == 0:
            print("\n⚠️  Collection is empty. Try running the test_api.py script first!")
            return

        # 2. Retrieve Sample Points
        # 'Scroll' allows us to page through data without a vector query
        print("\n🔍 Retrieving first 3 sample points to inspect content:")
        records, _ = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=3,
            with_payload=True,
            with_vectors=False  # Set to True if you want to see the actual number arrays
        )

        for i, point in enumerate(records, start=1):
            print("\n" + "="*50)
            print(f"POINT #{i} (ID: {point.id})")
            
            payload = point.payload
            if payload:
                # Display Type (Text/Table/Image)
                c_type = payload.get("content_type", "Unknown").upper()
                print(f"📂 Type:      {c_type}")
                
                # Display Metadata (Page number, etc.)
                meta = payload.get("metadata", {})
                print(f"ℹ️  Page:      {meta.get('page', 'N/A')}")
                
                # Display Text Content (Truncated for readability)
                text_content = payload.get("text", "")
                preview = (text_content[:150] + '...') if len(text_content) > 150 else text_content
                print(f"📝 Content:   \"{preview}\"")
            else:
                print("⚠️  No payload data found.")

        print("\n" + "="*50)
        print("✅ Verification complete. Data is correctly stored in Qdrant.")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Ensure Docker is running and the COLLECTION_NAME matches your .env file.")

if __name__ == "__main__":
    verify_data()