import fitz  # PyMuPDF
import pdfplumber
import pytesseract
from PIL import Image
import io
import zipfile
import xml.etree.ElementTree as ET

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
                    try:
                        extracted_text += pytesseract.image_to_string(img, lang="hin+eng") + "\n"
                    except Exception:
                        extracted_text += pytesseract.image_to_string(img) + "\n"
            except Exception:
                pass

        return extracted_text.strip()

    @staticmethod
    def extract_text_from_image(file_bytes: bytes, lang: str = "hin+eng") -> str:
        """Extracts text from an image with multilingual support (Hindi + English) and graceful fallback."""
        try:
            img = Image.open(io.BytesIO(file_bytes))
            try:
                return pytesseract.image_to_string(img, lang=lang).strip()
            except Exception:
                return pytesseract.image_to_string(img).strip()
        except Exception:
            return ""

    @staticmethod
    def extract_text_from_docx(file_bytes: bytes) -> str:
        """Extracts full document text from .docx file via standard OpenXML parsing."""
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                xml_content = z.read("word/document.xml")
                root = ET.fromstring(xml_content)
                paragraphs = []
                ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
                for p in root.iter(f"{{{ns['w']}}}p"):
                    texts = [node.text for node in p.iter(f"{{{ns['w']}}}t") if node.text]
                    if texts:
                        paragraphs.append("".join(texts))
                return "\n".join(paragraphs).strip()
        except Exception:
            return ""

    @staticmethod
    def extract_text_from_txt(file_bytes: bytes) -> str:
        """Decodes raw text/markdown/csv file content with UTF-8 fallback."""
        try:
            return file_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            try:
                return file_bytes.decode("latin-1").strip()
            except Exception:
                return ""

document_parser = DocumentParserService()