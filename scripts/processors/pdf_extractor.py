#!/usr/bin/env python3
"""
PDF Extractor Module
Extracts text content from PDF files containing bus route data.
"""

import os
import logging
from typing import Optional, Dict, Any
import PyPDF2
import pdfplumber
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Extracts text content from PDF files."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize PDF extractor.
        
        Args:
            config: Configuration dictionary with extraction settings
        """
        self.config = config or {}
        self.extraction_method = self.config.get('method', 'pdfplumber')
        self.dpi = self.config.get('dpi', 300)
        
    def extract_text(self, pdf_path: str, output_path: Optional[str] = None) -> str:
        """
        Extract text from PDF file.
        
        Args:
            pdf_path: Path to input PDF file
            output_path: Optional path to save extracted text
            
        Returns:
            Extracted text content
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        logger.info(f"Extracting text from {pdf_path}")
        
        if self.extraction_method == 'pdfplumber':
            text = self._extract_with_pdfplumber(pdf_path)
        else:
            text = self._extract_with_pypdf2(pdf_path)
            
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            logger.info(f"Extracted text saved to {output_path}")
            
        return text
        
    def _extract_with_pdfplumber(self, pdf_path: Path) -> str:
        """Extract text using pdfplumber library."""
        text_content = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(f"--- Page {page_num} ---\n")
                        text_content.append(page_text)
                        text_content.append("\n\n")
                        
        except Exception as e:
            logger.error(f"Error extracting text with pdfplumber: {e}")
            raise
            
        return ''.join(text_content)
        
    def _extract_with_pypdf2(self, pdf_path: Path) -> str:
        """Extract text using PyPDF2 library."""
        text_content = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(f"--- Page {page_num} ---\n")
                        text_content.append(page_text)
                        text_content.append("\n\n")
                        
        except Exception as e:
            logger.error(f"Error extracting text with PyPDF2: {e}")
            raise
            
        return ''.join(text_content)
        
    def extract_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF file.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary containing PDF metadata
        """
        pdf_path = Path(pdf_path)
        metadata = {}
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_info = pdf_reader.metadata
                
                if pdf_info:
                    metadata = {
                        'title': pdf_info.get('/Title', ''),
                        'author': pdf_info.get('/Author', ''),
                        'subject': pdf_info.get('/Subject', ''),
                        'creator': pdf_info.get('/Creator', ''),
                        'producer': pdf_info.get('/Producer', ''),
                        'creation_date': pdf_info.get('/CreationDate', ''),
                        'modification_date': pdf_info.get('/ModDate', ''),
                    }
                    
                metadata['page_count'] = len(pdf_reader.pages)
                metadata['file_size'] = pdf_path.stat().st_size
                
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            
        return metadata