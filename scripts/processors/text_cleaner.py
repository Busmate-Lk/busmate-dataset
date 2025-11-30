#!/usr/bin/env python3
"""
Text Cleaner Module
Cleans and normalizes text content extracted from PDFs.
"""

import re
import logging
import unicodedata
from typing import List, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class TextCleaner:
    """Cleans and normalizes extracted text content."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize text cleaner.
        
        Args:
            config: Configuration dictionary with cleaning settings
        """
        self.config = config or {}
        self.remove_duplicates = self.config.get('remove_duplicates', True)
        self.normalize_text = self.config.get('normalize_text', True)
        self.fix_encoding = self.config.get('fix_encoding', True)
        
    def clean_text(self, text: str, output_path: Optional[str] = None) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Input text to clean
            output_path: Optional path to save cleaned text
            
        Returns:
            Cleaned text content
        """
        logger.info("Starting text cleaning process")
        
        # Apply cleaning steps
        cleaned_text = text
        
        if self.fix_encoding:
            cleaned_text = self._fix_encoding_issues(cleaned_text)
            
        if self.normalize_text:
            cleaned_text = self._normalize_text(cleaned_text)
            
        cleaned_text = self._clean_formatting(cleaned_text)
        cleaned_text = self._remove_noise(cleaned_text)
        
        if self.remove_duplicates:
            cleaned_text = self._remove_duplicate_lines(cleaned_text)
            
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            logger.info(f"Cleaned text saved to {output_path}")
            
        logger.info("Text cleaning completed")
        return cleaned_text
        
    def _fix_encoding_issues(self, text: str) -> str:
        """Fix common encoding issues in extracted text."""
        # Common encoding fixes for Sri Lankan text
        encoding_fixes = {
            'à¶': 'ක',  # Sinhala letter Ka
            'à·': 'ා',  # Sinhala vowel Aa
            '®°': '්',  # Sinhala Al-lakuna (virama)
            # Add more encoding fixes as needed
        }
        
        for wrong, correct in encoding_fixes.items():
            text = text.replace(wrong, correct)
            
        # Normalize unicode characters
        text = unicodedata.normalize('NFC', text)
        
        return text
        
    def _normalize_text(self, text: str) -> str:
        """Normalize text formatting and characters."""
        # Convert to consistent line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Normalize whitespace
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double
        
        # Fix common OCR issues
        text = text.replace('|', 'I')  # Pipe to capital I
        text = text.replace('0', 'O')  # Zero to capital O where appropriate
        
        return text.strip()
        
    def _clean_formatting(self, text: str) -> str:
        """Clean formatting artifacts from PDF extraction."""
        # Remove page headers/footers patterns
        text = re.sub(r'--- Page \d+ ---\n?', '', text)
        
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Clean up route number patterns
        text = re.sub(r'Route\s*No\.?\s*:', 'Route:', text, flags=re.IGNORECASE)
        
        # Clean up operator patterns
        text = re.sub(r'Operator\s*:', 'Operator:', text, flags=re.IGNORECASE)
        
        return text
        
    def _remove_noise(self, text: str) -> str:
        """Remove noise and irrelevant content."""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
                
            # Skip lines that are just numbers or special characters
            if re.match(r'^[\d\s\-_.]+$', line):
                continue
                
            # Skip lines that look like headers or footers
            if len(line) < 3 or line.count(' ') > 20:
                continue
                
            cleaned_lines.append(line)
            
        return '\n'.join(cleaned_lines)
        
    def _remove_duplicate_lines(self, text: str) -> str:
        """Remove duplicate lines while preserving order."""
        lines = text.split('\n')
        seen = set()
        unique_lines = []
        
        for line in lines:
            line_clean = line.strip().lower()
            if line_clean not in seen:
                seen.add(line_clean)
                unique_lines.append(line)
                
        return '\n'.join(unique_lines)
        
    def extract_route_sections(self, text: str) -> List[Dict[str, str]]:
        """
        Extract individual route sections from cleaned text.
        
        Args:
            text: Cleaned text content
            
        Returns:
            List of dictionaries containing route sections
        """
        sections = []
        current_section = []
        in_route_section = False
        
        for line in text.split('\n'):
            line = line.strip()
            
            # Detect start of route section
            if re.search(r'route\s*(no\.?|number)\s*[:.]?\s*\d+', line, re.IGNORECASE):
                if current_section:
                    sections.append({
                        'content': '\n'.join(current_section),
                        'type': 'route_data'
                    })
                current_section = [line]
                in_route_section = True
            elif in_route_section and line:
                current_section.append(line)
            elif not line and current_section:
                # Empty line might indicate end of section
                continue
                
        # Add final section
        if current_section:
            sections.append({
                'content': '\n'.join(current_section),
                'type': 'route_data'
            })
            
        return sections