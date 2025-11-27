import requests
import os

# Configuration
# Ensure this matches the port defined in docker-compose.yml
API_URL = "http://localhost:8000/vectorize" 
# REPLACE THIS with the actual path to a PDF file on your machine
PDF_FILE_PATH = "AI_2.pdf" 

def test_vectorize_endpoint():
    """
    Tests the FastAPI /vectorize endpoint by uploading a PDF file.
    """
    # 1. Check if file exists
    if not os.path.exists(PDF_FILE_PATH):
        print(f"❌ Error: File not found at '{PDF_FILE_PATH}'")
        print("Please update the PDF_FILE_PATH variable in the script.")
        return

    print(f"🚀 Sending '{PDF_FILE_PATH}' to {API_URL}...")

    try:
        # 2. Open the file in binary mode
        with open(PDF_FILE_PATH, "rb") as f:
            # Prepare the multipart/form-data payload
            # 'file' must match the parameter name in the FastAPI function: 
            # def vectorize_pdf(file: UploadFile = File(...)):
            files = {"file": (os.path.basename(PDF_FILE_PATH), f, "application/pdf")}
            
            # 3. Send POST request
            response = requests.post(API_URL, files=files)

        # 4. Handle Response
        if response.status_code == 200:
            print("\n✅ Success! Server Response:")
            print("-----------------------------")
            print(response.json())
            print("-----------------------------")
        else:
            print(f"\n⚠️ Request failed with status code: {response.status_code}")
            print("Response details:")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error: Could not connect to {API_URL}.")
        print("Make sure your Docker container is running (docker-compose up).")
    except Exception as e:
        print(f"\n❌ An error occurred: {str(e)}")

if __name__ == "__main__":
    # Create a dummy file for testing if one doesn't exist
    if not os.path.exists(PDF_FILE_PATH) and PDF_FILE_PATH == "sample_doc.pdf":
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="This is a test PDF for the vectorization service.", ln=1, align="C")
        pdf.output("sample_doc.pdf")
        print("ℹ️  Created a dummy PDF 'sample_doc.pdf' for testing.")
        
    test_vectorize_endpoint()