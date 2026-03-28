"""
📄 PDF Reader
Extract text from uploaded PDF resume
Works on both local and Railway/cloud
"""

import pdfplumber
import os


def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    text = ""
    try:
        if not os.path.exists(file_path):
            return "❌ Error: File not found"

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        if not text.strip():
            return "❌ Error: Could not extract text from PDF. The PDF might be image-based."

    except Exception as e:
        text = f"❌ Error reading PDF: {str(e)}"

    return text.strip()
