from pdf2image import convert_from_path
import os

def pdf_to_images(pdf_path, output_folder):
    images = convert_from_path(pdf_path, dpi=300)
    image_paths = []
    
    for i, image in enumerate(images):
        image_path = f"{output_folder}/page_{i+1}.png"
        image.save(image_path, 'PNG')
        image_paths.append(image_path)
    
    return image_paths

# Usage
pdf_path = "bus_routes.pdf"
output_folder = "converted_images"
image_paths = pdf_to_images(pdf_path, output_folder)