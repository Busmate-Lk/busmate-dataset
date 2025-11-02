
import pytesseract
from PIL import Image
import os
import glob

def get_image_paths(folder_path):
    """Get all PNG images from the folder"""
    pattern = os.path.join(folder_path, "*.png")
    image_paths = glob.glob(pattern)
    image_paths.sort()  # Sort to maintain page order
    return image_paths

def extract_sinhala_text(image_path):
    """Extract Sinhala text from image using OCR"""
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Configure Tesseract for Sinhala
        custom_config = r'--oem 3 --psm 6 -l sin+eng'
        
        # Extract text
        text = pytesseract.image_to_string(img, config=custom_config, lang='sin')
        
        return text.strip()
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return ""

def process_all_pages(image_paths):
    """Process all images and extract text"""
    all_text = []
    for image_path in image_paths:
        print(f"Processing {image_path}...")
        text = extract_sinhala_text(image_path)
        all_text.append({
            'image_path': image_path,
            'text': text
        })
        print(f"Extracted text length: {len(text)} characters")
        if text:
            print(f"Preview: {text[:100]}...")
    
    return all_text

# Main execution
if __name__ == "__main__":
    # Configuration
    output_folder = "converted_images"
    
    # Get existing image paths
    image_paths = get_image_paths(output_folder)
    
    if not image_paths:
        print(f"No PNG images found in '{output_folder}' folder!")
        print("Please run the PDF conversion script first.")
    else:
        print(f"Found {len(image_paths)} images to process...")
        
        # Extract text from images
        extracted_data = process_all_pages(image_paths)
        
        # Save results
        with open("extracted_text.txt", "w", encoding="utf-8") as f:
            for i, data in enumerate(extracted_data):
                f.write(f"=== Page {i+1} ===\n")
                f.write(data['text'])
                f.write("\n\n")
        
        print(f"\nExtraction complete! Results saved to 'extracted_text.txt'")