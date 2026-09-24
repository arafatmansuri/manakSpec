import io
import zipfile
from typing import Dict, Any, List

def _escape_xml(text: Any) -> str:
    if text is None:
        return ""
    s = str(text)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

class PurePDFGenerator:
    """
    Dependency-free, pure-Python vector PDF generator adhering to Adobe PDF 1.4 specification.
    Produces high-fidelity, selectable vector text, tables, and headers with auto-pagination.
    """
    def __init__(self, page_width=595.28, page_height=841.89): # Standard A4 in points
        self.w = page_width
        self.h = page_height
        self.margin_x = 45.0
        self.margin_top = 45.0
        self.margin_bottom = 50.0
        self.content_w = self.w - (2 * self.margin_x)
        self.pages: List[str] = []
        self.current_page: List[str] = []
        self.y = self.h - self.margin_top

    def new_page(self):
        if self.current_page or not self.pages:
            self.pages.append("".join(self.current_page))
            self.current_page = []
        self.y = self.h - self.margin_top

    def ensure_space(self, height: float):
        if self.y - height < self.margin_bottom:
            self.new_page()

    def add_command(self, cmd: str):
        self.current_page.append(cmd)

    def draw_rect(self, x, y, w, h, fill_rgb=None, stroke_rgb=None, stroke_width=1.0):
        cmd = "q "
        if stroke_rgb:
            cmd += f"{stroke_rgb[0]:.3f} {stroke_rgb[1]:.3f} {stroke_rgb[2]:.3f} RG {stroke_width:.2f} w "
        if fill_rgb:
            cmd += f"{fill_rgb[0]:.3f} {fill_rgb[1]:.3f} {fill_rgb[2]:.3f} rg "
        cmd += f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re "
        if fill_rgb and stroke_rgb:
            cmd += "B Q\n"
        elif fill_rgb:
            cmd += "f Q\n"
        elif stroke_rgb:
            cmd += "S Q\n"
        else:
            cmd += "n Q\n"
        self.add_command(cmd)

    def draw_line(self, x1, y1, x2, y2, rgb=(0.7, 0.7, 0.7), width=0.8):
        cmd = f"q {rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} RG {width:.2f} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S Q\n"
        self.add_command(cmd)

    def escape(self, s: Any) -> str:
        if s is None:
            return ""
        text = str(s).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        # Transcode non-latin1 characters safely
        return "".join(c if ord(c) < 256 else "?" for c in text)

    def draw_text(self, text: str, font: str = "F1", size: float = 10.0, rgb=(0.1, 0.1, 0.1), x=None, y=None):
        if x is None:
            x = self.margin_x
        if y is None:
            y = self.y
        escaped = self.escape(text)
        cmd = f"BT /{font} {size:.2f} Tf {rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} rg {x:.2f} {y:.2f} Td ({escaped}) Tj ET\n"
        self.add_command(cmd)

    def draw_paragraph(self, text: str, font: str = "F1", size: float = 9.5, rgb=(0.2, 0.2, 0.2), line_height: float = 13.0, indent: float = 0.0, max_w: float = None):
        if not text:
            return
        if max_w is None:
            max_w = self.content_w - indent
        char_w = size * 0.52
        max_chars = max(10, int(max_w / char_w))

        for paragraph in text.split("\n"):
            words = paragraph.split()
            if not words:
                self.y -= line_height * 0.5
                continue

            current_line = []
            current_len = 0
            for word in words:
                if current_len + len(word) + 1 <= max_chars:
                    current_line.append(word)
                    current_len += len(word) + 1
                else:
                    self.ensure_space(line_height)
                    line_str = " ".join(current_line)
                    self.draw_text(line_str, font=font, size=size, rgb=rgb, x=self.margin_x + indent, y=self.y)
                    self.y -= line_height
                    current_line = [word]
                    current_len = len(word)

            if current_line:
                self.ensure_space(line_height)
                line_str = " ".join(current_line)
                self.draw_text(line_str, font=font, size=size, rgb=rgb, x=self.margin_x + indent, y=self.y)
                self.y -= line_height

    def to_bytes(self) -> bytes:
        if self.current_page:
            self.pages.append("".join(self.current_page))
            self.current_page = []

        total_pages = len(self.pages)
        if total_pages == 0:
            self.pages = ["BT /F1 12 Tf 50 750 Td (Empty Document) Tj ET\n"]
            total_pages = 1

        # Add page numbering and footer rule to each page
        for p_idx in range(total_pages):
            footer = f"q 0.7 0.7 0.7 RG 0.5 w 45 35 m {self.w - 45:.2f} 35 l S Q\n"
            footer += f"BT /F1 8 Tf 0.4 0.4 0.4 rg 45 22 Td (Government E-Procurement - Bureau of Indian Standards Framework) Tj ET\n"
            footer += f"BT /F1 8 Tf 0.4 0.4 0.4 rg {self.w - 110:.2f} 22 Td (Page {p_idx + 1} of {total_pages}) Tj ET\n"
            self.pages[p_idx] = self.pages[p_idx] + footer

        page_obj_ids = [6 + 2 * i for i in range(total_pages)]
        kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)

        objs = {}
        objs[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
        objs[2] = f"<< /Type /Pages /Kids [{kids_str}] /Count {total_pages} >>".encode("utf-8")
        objs[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
        objs[4] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
        objs[5] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>"

        for i, page_stream in enumerate(self.pages):
            page_id = 6 + 2 * i
            stream_id = 7 + 2 * i
            page_dict = f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.w:.2f} {self.h:.2f}] /Contents {stream_id} 0 R /Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >> >>".encode("utf-8")
            stream_bytes = page_stream.encode("latin-1", errors="replace")
            content_dict = f"<< /Length {len(stream_bytes)} >>\nstream\n".encode("utf-8") + stream_bytes + b"\nendstream"
            objs[page_id] = page_dict
            objs[stream_id] = content_dict

        buf = io.BytesIO()
        buf.write(b"%PDF-1.4\n")
        offsets = {}
        total_objs = 5 + 2 * total_pages

        for obj_id in range(1, total_objs + 1):
            offsets[obj_id] = buf.tell()
            buf.write(f"{obj_id} 0 obj\n".encode("utf-8"))
            buf.write(objs[obj_id])
            buf.write(b"\nendobj\n")

        xref_pos = buf.tell()
        buf.write(f"xref\n0 {total_objs + 1}\n".encode("utf-8"))
        buf.write(b"0000000000 65535 f \n")
        for obj_id in range(1, total_objs + 1):
            buf.write(f"{offsets[obj_id]:010d} 00000 n \n".encode("utf-8"))

        buf.write(f"trailer\n<< /Size {total_objs + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("utf-8"))
        return buf.getvalue()


class TenderDocumentExporter:
    @staticmethod
    def generate_markdown(synthesis: Dict[str, Any], title: str = "Tender Specification Schedule") -> str:
        """Generates a professional Markdown schedule of BIS compliance for procurement tenders."""
        overview = synthesis.get("overview", "")
        primary_stds = synthesis.get("primary_standards_summary", [])
        allied_refs = synthesis.get("allied_references", [])
        cert = synthesis.get("certification_details", {})
        tender_clause = synthesis.get("tender_clause", {})

        md = []
        md.append(f"# GOVERNMENT E-PROCUREMENT TECHNICAL COMPLIANCE SCHEDULE")
        md.append(f"**Document Title**: {title}")
        md.append(f"**Standardization Framework**: Bureau of Indian Standards (BIS) & Quality Control Orders (QCO)\n")
        md.append("---\n")

        # 1. Overview
        md.append("## 1. Scope & Executive Overview")
        md.append(f"{overview}\n")

        # 2. Primary Standards
        md.append("## 2. Applicable Primary Indian Standards")
        if primary_stds:
            md.append("| IS Number | Title | Publication Year | Status | Latest Amendment | Mandatory QCO |")
            md.append("| :--- | :--- | :---: | :---: | :--- | :---: |")
            for std in primary_stds:
                qco_flag = "YES (Mandatory)" if std.get("is_mandatory_qco") else "No"
                md.append(f"| {std.get('is_number')} | {std.get('title')} | {std.get('publication_year') or 'N/A'} | {std.get('status', 'Active')} | {std.get('latest_amendment') or 'None'} | {qco_flag} |")
        else:
            md.append("_No specific primary standards recorded._")
        md.append("")

        # 3. Categorized Allied Standards
        md.append("## 3. Allied & Cross-Referenced Standards Schedule")
        if allied_refs:
            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for ref in allied_refs:
                rtype = ref.get("relation_type", "Normative Reference")
                grouped.setdefault(rtype, []).append(ref)

            for cat, items in grouped.items():
                md.append(f"### 3.{list(grouped.keys()).index(cat)+1} {cat}s")
                for item in items:
                    code = f"**{item.get('related_is_number')}**: " if item.get('related_is_number') else ""
                    desc = item.get("title_or_description", "")
                    md.append(f"- {code}{desc} *(Parent: {item.get('parent_is_number')})*")
                md.append("")
        else:
            md.append("_No allied references documented._\n")

        # 4. Mandatory Certification
        md.append("## 4. Mandatory Certification & Quality Control Order (QCO) Requirements")
        if cert:
            md.append(f"- **Scheme Name**: {cert.get('scheme_name', 'N/A')}")
            md.append(f"- **Governing Body / Order**: {cert.get('governing_body_or_order', 'N/A')}")
            md.append(f"- **Certification Mark**: {cert.get('mark_type', 'N/A')}")
            reqs = cert.get("requirements", [])
            if reqs:
                md.append("- **Compliance Checklist**:")
                for r in reqs:
                    md.append(f"  - [x] {r}")
        else:
            md.append("_General inspection guidelines apply._")
        md.append("")

        # 5. Tender Clauses
        md.append("## 5. Model Tender Specifications & Attachment Clauses")
        if tender_clause:
            md.append(f"### Clause Title: {tender_clause.get('title', 'Technical Compliance')}\n")
            md.append(f"#### 5.1 Standards Compliance Clause\n{tender_clause.get('standard_compliance', '')}\n")
            md.append(f"#### 5.2 Mandatory Certification & QCO Clause\n{tender_clause.get('mandatory_cert_clause', '')}\n")
            
            tech_specs = tender_clause.get("technical_specifications", [])
            if tech_specs:
                md.append("#### 5.3 Detailed Technical Parameters")
                for spec in tech_specs:
                    md.append(f"- {spec}")
                md.append("")
            
            md.append(f"#### 5.4 Testing, Inspection & Verification Documentation\n{tender_clause.get('testing_and_documentation', '')}\n")
        md.append("---\n*Generated by Indian Standards Procurement AI Engine (ManakSpec)*")

        return "\n".join(md)

    @staticmethod
    def generate_text(synthesis: Dict[str, Any], title: str = "Tender Specification Schedule") -> str:
        """Generates a structured plain text (.txt) document suitable for terminal / text readers."""
        overview = synthesis.get("overview", "")
        primary_stds = synthesis.get("primary_standards_summary", [])
        allied_refs = synthesis.get("allied_references", [])
        cert = synthesis.get("certification_details", {})
        tender_clause = synthesis.get("tender_clause", {})

        sep = "=" * 80
        sub_sep = "-" * 80
        lines = []

        lines.append(sep)
        lines.append("GOVERNMENT E-PROCUREMENT TECHNICAL COMPLIANCE SCHEDULE")
        lines.append(f"Title: {title}")
        lines.append("Framework: Bureau of Indian Standards (BIS) & Quality Control Orders (QCO)")
        lines.append(sep)
        lines.append("")

        # 1. Overview
        lines.append("1. SCOPE & EXECUTIVE OVERVIEW")
        lines.append(sub_sep)
        lines.append(overview)
        lines.append("")

        # 2. Primary Standards
        lines.append("2. APPLICABLE PRIMARY INDIAN STANDARDS")
        lines.append(sub_sep)
        if primary_stds:
            for s in primary_stds:
                qco_status = "Mandatory QCO" if s.get("is_mandatory_qco") else "Voluntary"
                lines.append(f"* Standard   : {s.get('is_number')}")
                lines.append(f"  Title      : {s.get('title')}")
                lines.append(f"  Year       : {s.get('publication_year') or 'N/A'} | Status: {s.get('status', 'Active')}")
                lines.append(f"  Amendments : {s.get('latest_amendment') or 'None'} | Compliance: {qco_status}")
                lines.append("")
        else:
            lines.append("No primary standards specified.\n")

        # 3. Allied Standards
        lines.append("3. ALLIED & CROSS-REFERENCED STANDARDS")
        lines.append(sub_sep)
        if allied_refs:
            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for ref in allied_refs:
                rtype = ref.get("relation_type", "Normative Reference")
                grouped.setdefault(rtype, []).append(ref)

            for cat, items in grouped.items():
                lines.append(f"[{cat}]")
                for item in items:
                    code = f"{item.get('related_is_number')}: " if item.get('related_is_number') else ""
                    lines.append(f"  - {code}{item.get('title_or_description')} (Parent: {item.get('parent_is_number')})")
                lines.append("")
        else:
            lines.append("No allied standards specified.\n")

        # 4. Mandatory Certification
        lines.append("4. MANDATORY CERTIFICATION & QUALITY CONTROL ORDER (QCO)")
        lines.append(sub_sep)
        lines.append(f"Scheme Name    : {cert.get('scheme_name', 'N/A')}")
        lines.append(f"Governing Order: {cert.get('governing_body_or_order', 'N/A')}")
        lines.append(f"Standard Mark  : {cert.get('mark_type', 'N/A')}")
        reqs = cert.get("requirements", [])
        if reqs:
            lines.append("Key Requirements:")
            for r in reqs:
                lines.append(f"  [x] {r}")
        lines.append("")

        # 5. Tender Clauses
        lines.append("5. READY-TO-ATTACH MODEL TENDER CLAUSES")
        lines.append(sub_sep)
        lines.append(f"5.1 Standards Compliance Clause:\n{tender_clause.get('standard_compliance', '')}\n")
        lines.append(f"5.2 Mandatory QCO Compliance Clause:\n{tender_clause.get('mandatory_cert_clause', '')}\n")
        
        tech_specs = tender_clause.get("technical_specifications", [])
        if tech_specs:
            lines.append("5.3 Technical Specifications Checklist:")
            for sp in tech_specs:
                lines.append(f"  - {sp}")
            lines.append("")

        lines.append(f"5.4 Testing, Inspection & Verification Schedule:\n{tender_clause.get('testing_and_documentation', '')}\n")
        lines.append(sep)
        lines.append("Generated by Indian Standards Procurement AI Engine (ManakSpec)")
        lines.append(sep)

        return "\n".join(lines)

    @staticmethod
    def generate_docx(synthesis: Dict[str, Any], title: str = "Tender Specification Schedule") -> bytes:
        """
        Creates a genuine OpenXML .docx file in memory containing the complete 
        procurement specification schedule with headings, tables, and formatted clauses.
        """
        overview = synthesis.get("overview", "")
        primary_stds = synthesis.get("primary_standards_summary", [])
        allied_refs = synthesis.get("allied_references", [])
        cert = synthesis.get("certification_details", {})
        tender_clause = synthesis.get("tender_clause", {})

        doc_body = []

        # Title
        doc_body.append(f"""
        <w:p>
            <w:pPr><w:jc w:val="center"/><w:spacing w:after="120"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="36"/><w:color w:val="1F4E79"/><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/></w:rPr>
            <w:t>GOVERNMENT E-PROCUREMENT TECHNICAL COMPLIANCE SCHEDULE</w:t></w:r>
        </w:p>
        <w:p>
            <w:pPr><w:jc w:val="center"/><w:spacing w:after="280"/></w:pPr>
            <w:r><w:rPr><w:i/><w:sz w:val="24"/><w:color w:val="595959"/></w:rPr>
            <w:t>{_escape_xml(title)} - Bureau of Indian Standards (BIS) Framework</w:t></w:r>
        </w:p>
        """)

        # Section 1: Overview
        doc_body.append(f"""
        <w:p><w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="2E75B6"/></w:rPr>
            <w:t>1. Scope &amp; Executive Overview</w:t></w:r>
        </w:p>
        <w:p><w:pPr><w:spacing w:after="180"/></w:pPr>
            <w:r><w:rPr><w:sz w:val="22"/></w:rPr><w:t>{_escape_xml(overview)}</w:t></w:r>
        </w:p>
        """)

        # Section 2: Primary Standards Table
        doc_body.append(f"""
        <w:p><w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="2E75B6"/></w:rPr>
            <w:t>2. Applicable Primary Indian Standards</w:t></w:r>
        </w:p>
        """)

        if primary_stds:
            table_xml = ["""
            <w:tbl>
                <w:tblPr>
                    <w:tblW w:w="9200" w:type="dxa"/>
                    <w:tblBorders>
                        <w:top w:val="single" w:sz="6" w:space="0" w:color="D3D3D3"/>
                        <w:left w:val="single" w:sz="6" w:space="0" w:color="D3D3D3"/>
                        <w:bottom w:val="single" w:sz="6" w:space="0" w:color="D3D3D3"/>
                        <w:right w:val="single" w:sz="6" w:space="0" w:color="D3D3D3"/>
                        <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E0E0E0"/>
                        <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E0E0E0"/>
                    </w:tblBorders>
                </w:tblPr>
                <w:tr>
                    <w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="2E75B6"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="20"/></w:rPr><w:t>IS Number</w:t></w:r></w:p></w:tc>
                    <w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="2E75B6"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="20"/></w:rPr><w:t>Standard Title</w:t></w:r></w:p></w:tc>
                    <w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="2E75B6"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="20"/></w:rPr><w:t>Year</w:t></w:r></w:p></w:tc>
                    <w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="2E75B6"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="20"/></w:rPr><w:t>Status</w:t></w:r></w:p></w:tc>
                    <w:tc><w:tcPr><w:shd w:val="clear" w:color="auto" w:fill="2E75B6"/></w:tcPr><w:p><w:r><w:rPr><w:b/><w:color w:val="FFFFFF"/><w:sz w:val="20"/></w:rPr><w:t>QCO Order</w:t></w:r></w:p></w:tc>
                </w:tr>
            """]
            for std in primary_stds:
                qco_text = "Mandatory" if std.get("is_mandatory_qco") else "Voluntary"
                table_xml.append(f"""
                <w:tr>
                    <w:tc><w:p><w:r><w:rPr><w:b/><w:sz w:val="20"/></w:rPr><w:t>{_escape_xml(std.get('is_number'))}</w:t></w:r></w:p></w:tc>
                    <w:tc><w:p><w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{_escape_xml(std.get('title'))}</w:t></w:r></w:p></w:tc>
                    <w:tc><w:p><w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{_escape_xml(std.get('publication_year') or 'N/A')}</w:t></w:r></w:p></w:tc>
                    <w:tc><w:p><w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{_escape_xml(std.get('status', 'Active'))}</w:t></w:r></w:p></w:tc>
                    <w:tc><w:p><w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{_escape_xml(qco_text)}</w:t></w:r></w:p></w:tc>
                </w:tr>
                """)
            table_xml.append("</w:tbl>")
            doc_body.append("".join(table_xml))

        # Section 3: Allied Standards
        doc_body.append(f"""
        <w:p><w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="2E75B6"/></w:rPr>
            <w:t>3. Allied, Normative &amp; Test Method Standards</w:t></w:r>
        </w:p>
        """)

        if allied_refs:
            grouped_refs: Dict[str, List[Dict[str, Any]]] = {}
            for ref in allied_refs:
                rtype = ref.get("relation_type", "Normative Reference")
                grouped_refs.setdefault(rtype, []).append(ref)

            for cat_name, items in grouped_refs.items():
                doc_body.append(f"""
                <w:p><w:pPr><w:spacing w:before="120" w:after="60"/></w:pPr>
                    <w:r><w:rPr><w:b/><w:sz w:val="24"/><w:color w:val="1F4E79"/></w:rPr>
                    <w:t>Category: {_escape_xml(cat_name)}</w:t></w:r>
                </w:p>
                """)
                for item in items:
                    ref_code = f"{item.get('related_is_number')}: " if item.get('related_is_number') else ""
                    doc_body.append(f"""
                    <w:p><w:pPr><w:spacing w:after="40"/><w:ind w:left="360"/></w:pPr>
                        <w:r><w:rPr><w:sz w:val="20"/><w:b/></w:rPr><w:t>• {_escape_xml(ref_code)}</w:t></w:r>
                        <w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{_escape_xml(item.get('title_or_description'))} (Parent: {_escape_xml(item.get('parent_is_number'))})</w:t></w:r>
                    </w:p>
                    """)
        else:
            doc_body.append("""
            <w:p><w:pPr><w:spacing w:after="120"/></w:pPr>
                <w:r><w:rPr><w:i/><w:sz w:val="20"/></w:rPr><w:t>No allied standards identified.</w:t></w:r>
            </w:p>
            """)

        # Section 4: Mandatory Certification
        doc_body.append(f"""
        <w:p><w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="2E75B6"/></w:rPr>
            <w:t>4. Mandatory Certification &amp; Quality Control Order (QCO)</w:t></w:r>
        </w:p>
        <w:p><w:pPr><w:spacing w:after="60"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="22"/></w:rPr><w:t>Certification Scheme: </w:t></w:r>
            <w:r><w:rPr><w:sz w:val="22"/></w:rPr><w:t>{_escape_xml(cert.get('scheme_name', 'N/A'))}</w:t></w:r>
        </w:p>
        <w:p><w:pPr><w:spacing w:after="60"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="22"/></w:rPr><w:t>Governing Order / Authority: </w:t></w:r>
            <w:r><w:rPr><w:sz w:val="22"/></w:rPr><w:t>{_escape_xml(cert.get('governing_body_or_order', 'N/A'))}</w:t></w:r>
        </w:p>
        <w:p><w:pPr><w:spacing w:after="120"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="22"/></w:rPr><w:t>Standard Mark: </w:t></w:r>
            <w:r><w:rPr><w:sz w:val="22"/></w:rPr><w:t>{_escape_xml(cert.get('mark_type', 'N/A'))}</w:t></w:r>
        </w:p>
        """)

        # Section 5: Tender Clauses
        doc_body.append(f"""
        <w:p><w:pPr><w:spacing w:before="240" w:after="120"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="28"/><w:color w:val="2E75B6"/></w:rPr>
            <w:t>5. Ready-to-Attach Model Tender Clauses</w:t></w:r>
        </w:p>
        <w:p><w:pPr><w:spacing w:before="120" w:after="60"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="1F4E79"/></w:rPr>
            <w:t>5.1 Standards Compliance Clause</w:t></w:r>
        </w:p>
        <w:p><w:pPr><w:spacing w:after="120"/></w:pPr>
            <w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{_escape_xml(tender_clause.get('standard_compliance', ''))}</w:t></w:r>
        </w:p>
        <w:p><w:pPr><w:spacing w:before="120" w:after="60"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="1F4E79"/></w:rPr>
            <w:t>5.2 Mandatory QCO Compliance Clause</w:t></w:r>
        </w:p>
        <w:p><w:pPr><w:spacing w:after="120"/></w:pPr>
            <w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{_escape_xml(tender_clause.get('mandatory_cert_clause', ''))}</w:t></w:r>
        </w:p>
        <w:p><w:pPr><w:spacing w:before="120" w:after="60"/></w:pPr>
            <w:r><w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="1F4E79"/></w:rPr>
            <w:t>5.3 Inspection &amp; Test Certificate Schedule</w:t></w:r>
        </w:p>
        <w:p><w:pPr><w:spacing w:after="120"/></w:pPr>
            <w:r><w:rPr><w:sz w:val="20"/></w:rPr><w:t>{_escape_xml(tender_clause.get('testing_and_documentation', ''))}</w:t></w:r>
        </w:p>
        """)

        # Assemble full document XML
        full_document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
            <w:body>
                {''.join(doc_body)}
                <w:sectPr>
                    <w:pgSz w:w="11906" w:h="16838"/>
                    <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>
                </w:sectPr>
            </w:body>
        </w:document>
        """

        # Build in-memory ZIP package
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
            content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
                <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
                <Default Extension="xml" ContentType="application/xml"/>
                <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
            </Types>
            """
            z.writestr("[Content_Types].xml", content_types_xml.strip().encode("utf-8"))

            rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
            <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
                <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
            </Relationships>
            """
            z.writestr("_rels/.rels", rels_xml.strip().encode("utf-8"))

            z.writestr("word/document.xml", full_document_xml.strip().encode("utf-8"))

        return zip_buffer.getvalue()

    @staticmethod
    def generate_pdf(synthesis: Dict[str, Any], title: str = "Tender Specification Schedule") -> bytes:
        """
        Creates an Adobe PDF 1.4 compliant vector document with banners,
        data tables, grouped allied standards, and tender specification clauses.
        """
        pdf = PurePDFGenerator()

        overview = synthesis.get("overview", "")
        primary_stds = synthesis.get("primary_standards_summary", [])
        allied_refs = synthesis.get("allied_references", [])
        cert = synthesis.get("certification_details", {})
        tender_clause = synthesis.get("tender_clause", {})

        # 1. Header Banner
        banner_h = 65.0
        pdf.draw_rect(pdf.margin_x, pdf.y - banner_h + 10, pdf.content_w, banner_h, fill_rgb=(0.12, 0.31, 0.47))
        pdf.draw_text("GOVERNMENT E-PROCUREMENT TECHNICAL COMPLIANCE SCHEDULE", font="F2", size=13.0, rgb=(1.0, 1.0, 1.0), x=pdf.margin_x + 12, y=pdf.y - 12)
        pdf.draw_text("Bureau of Indian Standards (BIS) & Quality Control Orders (QCO) Framework", font="F1", size=8.5, rgb=(0.85, 0.90, 0.96), x=pdf.margin_x + 12, y=pdf.y - 27)
        pdf.draw_text(f"Subject: {title}", font="F3", size=9.0, rgb=(1.0, 0.85, 0.40), x=pdf.margin_x + 12, y=pdf.y - 43)
        pdf.y -= (banner_h + 15)

        # 2. Section 1: Scope & Overview
        pdf.ensure_space(40)
        pdf.draw_text("1. SCOPE & EXECUTIVE OVERVIEW", font="F2", size=11.0, rgb=(0.18, 0.46, 0.71))
        pdf.y -= 4
        pdf.draw_line(pdf.margin_x, pdf.y, pdf.margin_x + pdf.content_w, pdf.y, rgb=(0.18, 0.46, 0.71), width=1.0)
        pdf.y -= 12
        pdf.draw_paragraph(overview, font="F1", size=9.0, rgb=(0.2, 0.2, 0.2), line_height=12.5)
        pdf.y -= 12

        # 3. Section 2: Primary Standards Table
        pdf.ensure_space(50)
        pdf.draw_text("2. APPLICABLE PRIMARY INDIAN STANDARDS", font="F2", size=11.0, rgb=(0.18, 0.46, 0.71))
        pdf.y -= 4
        pdf.draw_line(pdf.margin_x, pdf.y, pdf.margin_x + pdf.content_w, pdf.y, rgb=(0.18, 0.46, 0.71), width=1.0)
        pdf.y -= 14

        if primary_stds:
            headers = ["IS Number", "Title", "Year", "Status", "QCO Order"]
            col_widths = [95.0, 200.0, 45.0, 75.0, 90.0]
            row_h = 18.0

            # Table Header
            pdf.ensure_space(row_h * 2)
            pdf.draw_rect(pdf.margin_x, pdf.y - row_h + 3, pdf.content_w, row_h, fill_rgb=(0.12, 0.31, 0.47))
            cur_x = pdf.margin_x
            for i, h in enumerate(headers):
                pdf.draw_text(h, font="F2", size=8.5, rgb=(1.0, 1.0, 1.0), x=cur_x + 4, y=pdf.y - 10)
                cur_x += col_widths[i]
            pdf.y -= row_h

            # Table Rows
            for r_idx, s in enumerate(primary_stds):
                pdf.ensure_space(row_h)
                bg = (0.95, 0.96, 0.98) if r_idx % 2 == 1 else (1.0, 1.0, 1.0)
                pdf.draw_rect(pdf.margin_x, pdf.y - row_h + 3, pdf.content_w, row_h, fill_rgb=bg, stroke_rgb=(0.85, 0.85, 0.85), stroke_width=0.5)
                
                qco_txt = "Mandatory QCO" if s.get("is_mandatory_qco") else "Voluntary"
                vals = [
                    s.get("is_number", "N/A"),
                    (s.get("title") or "")[:42],
                    str(s.get("publication_year") or "N/A"),
                    s.get("status", "Active"),
                    qco_txt
                ]
                cur_x = pdf.margin_x
                for i, v in enumerate(vals):
                    fnt = "F2" if i == 0 else "F1"
                    rgb_val = (0.7, 0.1, 0.1) if i == 4 and "Mandatory" in v else (0.15, 0.15, 0.15)
                    pdf.draw_text(v, font=fnt, size=8.0, rgb=rgb_val, x=cur_x + 4, y=pdf.y - 10)
                    cur_x += col_widths[i]
                pdf.y -= row_h
            pdf.y -= 10
        else:
            pdf.draw_paragraph("No primary standards specified.", font="F3", size=9.0)
            pdf.y -= 10

        # 4. Section 3: Allied Standards
        pdf.ensure_space(45)
        pdf.draw_text("3. ALLIED & CROSS-REFERENCED STANDARDS SCHEDULE", font="F2", size=11.0, rgb=(0.18, 0.46, 0.71))
        pdf.y -= 4
        pdf.draw_line(pdf.margin_x, pdf.y, pdf.margin_x + pdf.content_w, pdf.y, rgb=(0.18, 0.46, 0.71), width=1.0)
        pdf.y -= 12

        if allied_refs:
            grouped: Dict[str, List[Dict[str, Any]]] = {}
            for ref in allied_refs:
                rtype = ref.get("relation_type", "Normative Reference")
                grouped.setdefault(rtype, []).append(ref)

            for cat, items in grouped.items():
                pdf.ensure_space(25)
                pdf.draw_text(f"• Category: {cat}", font="F2", size=9.5, rgb=(0.12, 0.31, 0.47), x=pdf.margin_x + 5)
                pdf.y -= 14
                for item in items:
                    pdf.ensure_space(14)
                    code_prefix = f"{item.get('related_is_number')}: " if item.get('related_is_number') else ""
                    desc = f"{code_prefix}{item.get('title_or_description')} (Parent: {item.get('parent_is_number')})"
                    pdf.draw_paragraph(f"- {desc}", font="F1", size=8.5, rgb=(0.2, 0.2, 0.2), line_height=11.5, indent=15.0)
                pdf.y -= 4
            pdf.y -= 6
        else:
            pdf.draw_paragraph("No allied standards identified.", font="F3", size=9.0)
            pdf.y -= 10

        # 5. Section 4: Mandatory Certification
        pdf.ensure_space(45)
        pdf.draw_text("4. MANDATORY CERTIFICATION & QUALITY CONTROL ORDERS (QCO)", font="F2", size=11.0, rgb=(0.18, 0.46, 0.71))
        pdf.y -= 4
        pdf.draw_line(pdf.margin_x, pdf.y, pdf.margin_x + pdf.content_w, pdf.y, rgb=(0.18, 0.46, 0.71), width=1.0)
        pdf.y -= 12

        if cert:
            cert_lines = [
                f"Certification Scheme : {cert.get('scheme_name', 'N/A')}",
                f"Governing Order     : {cert.get('governing_body_or_order', 'N/A')}",
                f"Standard Mark       : {cert.get('mark_type', 'N/A')}"
            ]
            for cl in cert_lines:
                pdf.ensure_space(14)
                pdf.draw_text(cl, font="F1", size=8.8, rgb=(0.15, 0.15, 0.15), x=pdf.margin_x + 8)
                pdf.y -= 13

            reqs = cert.get("requirements", [])
            if reqs:
                pdf.y -= 4
                pdf.draw_text("Compliance Requirements Checklist:", font="F2", size=8.8, rgb=(0.15, 0.15, 0.15), x=pdf.margin_x + 8)
                pdf.y -= 12
                for r in reqs:
                    pdf.ensure_space(13)
                    pdf.draw_text(f"[x] {r}", font="F1", size=8.5, rgb=(0.2, 0.2, 0.2), x=pdf.margin_x + 18)
                    pdf.y -= 12
            pdf.y -= 10

        # 6. Section 5: Model Tender Clauses
        pdf.ensure_space(50)
        pdf.draw_text("5. READY-TO-ATTACH MODEL TENDER CLAUSES", font="F2", size=11.0, rgb=(0.18, 0.46, 0.71))
        pdf.y -= 4
        pdf.draw_line(pdf.margin_x, pdf.y, pdf.margin_x + pdf.content_w, pdf.y, rgb=(0.18, 0.46, 0.71), width=1.0)
        pdf.y -= 14

        if tender_clause:
            # 5.1 Standards Compliance Clause
            pdf.ensure_space(30)
            pdf.draw_text("5.1 Standards Compliance Clause", font="F2", size=9.5, rgb=(0.12, 0.31, 0.47), x=pdf.margin_x + 5)
            pdf.y -= 13
            pdf.draw_paragraph(tender_clause.get("standard_compliance", ""), font="F1", size=8.5, rgb=(0.2, 0.2, 0.2), line_height=11.5, indent=8.0)
            pdf.y -= 8

            # 5.2 Mandatory QCO Clause
            pdf.ensure_space(30)
            pdf.draw_text("5.2 Mandatory Quality Control Order (QCO) Clause", font="F2", size=9.5, rgb=(0.12, 0.31, 0.47), x=pdf.margin_x + 5)
            pdf.y -= 13
            pdf.draw_paragraph(tender_clause.get("mandatory_cert_clause", ""), font="F1", size=8.5, rgb=(0.2, 0.2, 0.2), line_height=11.5, indent=8.0)
            pdf.y -= 8

            # 5.3 Technical Specifications
            tech_specs = tender_clause.get("technical_specifications", [])
            if tech_specs:
                pdf.ensure_space(30)
                pdf.draw_text("5.3 Technical Parameters Checklist", font="F2", size=9.5, rgb=(0.12, 0.31, 0.47), x=pdf.margin_x + 5)
                pdf.y -= 13
                for sp in tech_specs:
                    pdf.ensure_space(13)
                    pdf.draw_paragraph(f"• {sp}", font="F1", size=8.5, rgb=(0.2, 0.2, 0.2), line_height=11.5, indent=12.0)
                pdf.y -= 8

            # 5.4 Testing & Documentation
            pdf.ensure_space(30)
            pdf.draw_text("5.4 Testing, Inspection & Verification Documentation", font="F2", size=9.5, rgb=(0.12, 0.31, 0.47), x=pdf.margin_x + 5)
            pdf.y -= 13
            pdf.draw_paragraph(tender_clause.get("testing_and_documentation", ""), font="F1", size=8.5, rgb=(0.2, 0.2, 0.2), line_height=11.5, indent=8.0)

        return pdf.to_bytes()

tender_exporter = TenderDocumentExporter()
