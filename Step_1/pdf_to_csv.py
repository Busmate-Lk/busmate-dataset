#!/usr/bin/env python3
"""PDF Fare Table to CSV Converter"""

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import pdf2image
import pandas as pd
import re
import os
import sys

PDF_FILE = 'fare_document.pdf'
OUTPUT_CSV = 'fare_table_output.csv'
OCR_LANG = 'sin+eng'
DPI = 300

def check_dependencies():
    print("Checking dependencies...")
    try:
        version = pytesseract.get_tesseract_version()
        print(f"✓ Tesseract OCR: v{version}")
    except Exception as e:
        print("✗ Tesseract not found!")
        return False
    
    try:
        langs = pytesseract.get_languages()
        if 'sin' in langs:
            print("✓ Sinhala language pack: Available")
        else:
            print("✗ Sinhala language pack not found!")
            return False
    except Exception as e:
        print(f"✗ Error checking languages: {e}")
        return False
    
    if os.path.exists(PDF_FILE):
        print(f"✓ PDF file found: {PDF_FILE}")
    else:
        print(f"✗ PDF file not found: {PDF_FILE}")
        return False
    
    print()
    return True

def preprocess_image(image):
    if image.mode != 'L':
        image = image.convert('L')
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.5)
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.5)
    image = image.filter(ImageFilter.MedianFilter(size=3))
    image = image.filter(ImageFilter.SHARPEN)
    return image

def convert_pdf_to_images(pdf_path):
    print("Converting PDF to images...")
    try:
        images = pdf2image.convert_from_path(pdf_path, dpi=DPI, fmt='png')
        print(f"✓ Converted {len(images)} page(s)")
        return images
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def extract_text_from_image(image, enhance=True):
    try:
        if enhance:
            image = preprocess_image(image)
        text = pytesseract.image_to_string(image, lang=OCR_LANG, config='--psm 6 --oem 3')
        return text
    except Exception as e:
        print(f"✗ OCR Error: {e}")
        return None

def parse_fare_data(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    fare_data = []
    pattern = re.compile(r'^(\d+)\s+([\d.]+)$')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        match = pattern.match(line)
        if match:
            route_num = match.group(1)
            fare = match.group(2)
            location = "Unknown"
            for j in range(max(0, i-3), i):
                prev_line = lines[j]
                if prev_line and not pattern.match(prev_line):
                    if len(prev_line) > 2:
                        location = prev_line
                        break
            fare_data.append({
                'Route_Number': int(route_num),
                'Location': location,
                'Fare_LKR': float(fare)
            })
        i += 1
    return fare_data

def save_to_csv(data, output_file):
    if not data:
        print("✗ No data to save")
        return False
    try:
        df = pd.DataFrame(data)
        df = df.sort_values('Route_Number')
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n✓ Saved {len(data)} rows to {output_file}")
        return True
    except Exception as e:
        print(f"✗ Error saving: {e}")
        return False

def display_summary(data):
    if not data:
        return
    df = pd.DataFrame(data)
    print("\n" + "="*60)
    print("DATA SUMMARY")
    print("="*60)
    print(f"Total entries: {len(df)}")
    print(f"Routes: {df['Route_Number'].min()} to {df['Route_Number'].max()}")
    print(f"Fares: LKR {df['Fare_LKR'].min():.2f} to {df['Fare_LKR'].max():.2f}")
    print(f"Average: LKR {df['Fare_LKR'].mean():.2f}")
    print("\nFirst 10 entries:")
    print(df.head(10).to_string(index=False))

def main():
    print("="*60)
    print("PDF FARE TABLE TO CSV CONVERTER")
    print("="*60)
    print()
    
    if not check_dependencies():
        sys.exit(1)
    
    images = convert_pdf_to_images(PDF_FILE)
    if not images:
        sys.exit(1)
    
    all_fare_data = []
    for page_num, image in enumerate(images, 1):
        print(f"\n--- Page {page_num}/{len(images)} ---")
        image.save(f'page_{page_num}.png')
        print(f"✓ Saved: page_{page_num}.png")
        
        text = extract_text_from_image(image)
        if text:
            with open(f'page_{page_num}_ocr.txt', 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"✓ OCR saved: page_{page_num}_ocr.txt")
            
            fare_data = parse_fare_data(text)
            print(f"✓ Extracted {len(fare_data)} entries")
            all_fare_data.extend(fare_data)
    
    print("\n" + "="*60)
    if all_fare_data:
        display_summary(all_fare_data)
        if save_to_csv(all_fare_data, OUTPUT_CSV):
            print("\n✅ SUCCESS! Check {OUTPUT_CSV}")
    else:
        print("❌ No data extracted")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
