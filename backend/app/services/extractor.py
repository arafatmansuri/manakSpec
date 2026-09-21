import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

def extract_text_from_file_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Extracts text from an uploaded file (PDF or Image).
    Uses PyMuPDF layout parsing and falls back to Tesseract OCR for scanned documents.
    """
    ext = filename.lower().split('.')[-1]

    # Handle Image Uploads (PNG, JPG, JPEG, TIFF)
    if ext in ['png', 'jpg', 'jpeg', 'tiff', 'bmp']:
        image = Image.open(io.BytesIO(file_bytes))
        ocr_text = pytesseract.image_to_string(image)
        return ocr_text.strip()

    # Handle PDF Uploads
    elif ext == 'pdf':
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        extracted_text = ""
        
        for page in doc:
            text = page.get_text()
            # If text is minimal (e.g. scanned PDF page), run OCR fallback
            if len(text.strip()) < 50:
                pix = page.get_pixmap()
                img = Image.open(io.BytesIO(pix.tobytes()))
                ocr_text = pytesseract.image_to_string(img)
                extracted_text += f"\n{ocr_text}"
            else:
                extracted_text += f"\n{text}"
                
        return extracted_text.strip()

    else:
        # Fallback for plain text files (.txt, .md)
        try:
            return file_bytes.decode('utf-8')
        except Exception:
            raise ValueError("Unsupported file format provided.")