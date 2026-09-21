import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image
import io

class DocumentParserService:
    @staticmethod
    def extract_text_from_pdf(file_bytes: bytes) -> str:
        extracted_text = ""
        # 1. Try PyMuPDF for fast extraction
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                extracted_text += page.get_text() + "\n"
        except Exception:
            extracted_text = ""

        # 2. Fallback to pdfplumber for table preservation if PyMuPDF yielded low character count
        if len(extracted_text.strip()) < 50:
            try:
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    extracted_text = ""
                    for page in pdf.pages:
                        extracted_text += (page.extract_text() or "") + "\n"
            except Exception:
                pass

        # 3. Fallback to OCR if page contains purely scanned images
        if len(extracted_text.strip()) < 20:
            try:
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                extracted_text = ""
                for page in doc:
                    pix = page.get_pixmap()
                    img = Image.open(io.BytesIO(pix.tobytes()))
                    extracted_text += pytesseract.image_to_string(img) + "\n"
            except Exception:
                pass

        return extracted_text.strip()

    @staticmethod
    def extract_text_from_image(file_bytes: bytes) -> str:
        img = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(img).strip()

document_parser = DocumentParserService()