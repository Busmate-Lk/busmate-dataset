import re
import pandas as pd
import os
from pathlib import Path

def clean_stop_name(name):
    """
    Clean common OCR errors in Sinhala stop names
    """
    corrections = {
        'චිශ්ච චිදා9ාලය': 'විද්‍යාලය',
        'චිදා9ාලය': 'විද්‍යාලය',
        'හංදිය': 'හන්දිය',
        'හංදියට': 'හන්දියට',
        'Bae': 'බදුල්ල',
        'ට්‍රැක්මෙ?': 'ට්‍රැක්මෙන්',
        'දෝොණිය': 'දෝණිය',
        'චරකාපොල': 'දරකාපොල',
        'චේචැල්දෝොණිය': 'දෙහිවලගොඩ',
        'BO': '',
        'Ned': '',
        'dz': '',
        'ame': '',
        'arg': '',
        'os!': ''
    }
    
    for error, correction in corrections.items():
        name = name.replace(error, correction)
    
    # Remove extra spaces and clean up
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def extract_route_data(page_text):
    """
    Extract route information and stops from a single page text
    """
    try:
        # Extract route number
        route_match = re.search(r'මා(ර්ග|ථ්ග)\s*අංක\s*:\s*([^\n]+)', page_text)
        if route_match:
            route_number = route_match.group(2).strip()
        else:
            # Alternative pattern for route number
            route_match = re.search(r'අංක\s*:\s*([^\n]+)', page_text)
            route_number = route_match.group(1).strip() if route_match else "Unknown"
        
        # Extract route description
        route_desc_match = re.search(r'අංක[^\n]+\n([^\n]+)', page_text)
        route_desc = route_desc_match.group(1).strip() if route_desc_match else ""
        
        # Clean route description
        route_desc = clean_stop_name(route_desc)
        
        # Extract stops with fares - multiple patterns to handle different formats
        stops = []
        
        # Pattern 1: Number, fare, stop name (most common)
        stop_pattern1 = r'(\d+)\s+([\d.]+)\s*\]\s*([^\n]+?)(?=\n\d+\s+[\d.]|$)'
        # Pattern 2: Number, stop name (when fare is missing)
        stop_pattern2 = r'(\d+)\s+([^\n]+?)(?=\n\d+\s+[^\n]|$)'
        
        # Try pattern 1 first
        for match in re.finditer(stop_pattern1, page_text):
            stop_num = int(match.group(1))
            fare = float(match.group(2))
            stop_name = match.group(3).strip()
            stop_name = clean_stop_name(stop_name)
            
            stops.append({
                'stop_sequence': stop_num,
                'stop_name': stop_name,
                'fare_from_start': fare
            })
        
        # If no stops found with pattern 1, try pattern 2
        if not stops:
            for match in re.finditer(stop_pattern2, page_text):
                stop_num = int(match.group(1))
                stop_name = match.group(2).strip()
                stop_name = clean_stop_name(stop_name)
                
                stops.append({
                    'stop_sequence': stop_num,
                    'stop_name': stop_name,
                    'fare_from_start': 0.00  # Default fare
                })
        
        return {
            'route_number': route_number,
            'route_name': route_desc,
            'stops': stops
        }
    
    except Exception as e:
        print(f"Error extracting route data: {e}")
        return None

def process_text_file(input_file_path):
    """
    Process the entire text file and extract all routes
    """
    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Split content by pages
        pages = re.split(r'=== Page \d+ ===', content)
        
        all_routes = []
        
        for i, page_text in enumerate(pages):
            if page_text.strip():  # Skip empty pages
                print(f"Processing page {i+1}...")
                route_data = extract_route_data(page_text)
                if route_data and route_data['stops']:
                    all_routes.append(route_data)
                    print(f"  Found route {route_data['route_number']} with {len(route_data['stops'])} stops")
                else:
                    print(f"  No route data found on page {i+1}")
        
        return all_routes
    
    except Exception as e:
        print(f"Error processing file: {e}")
        return []

def create_csv_output(routes_data, output_dir):
    """
    Convert structured data to CSV format and save files
    """
    if not routes_data:
        print("No route data to process!")
        return
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)
    
    # Create main consolidated CSV
    main_csv_data = []
    
    for route in routes_data:
        for stop in route['stops']:
            main_csv_data.append({
                'route_number': route['route_number'],
                'route_name': route['route_name'],
                'stop_sequence': stop['stop_sequence'],
                'stop_id': f"{route['route_number']}_{stop['stop_sequence']:03d}",
                'stop_name': stop['stop_name'],
                'fare_from_start': stop['fare_from_start']
            })
    
    # Save main consolidated CSV
    main_df = pd.DataFrame(main_csv_data)
    main_output_path = os.path.join(output_dir, 'all_bus_routes.csv')
    main_df.to_csv(main_output_path, index=False, encoding='utf-8')
    print(f"Main CSV saved: {main_output_path}")
    
    # Also save individual route CSVs
    for route in routes_data:
        route_df = pd.DataFrame([
            {
                'route_number': route['route_number'],
                'route_name': route['route_name'],
                'stop_sequence': stop['stop_sequence'],
                'stop_id': f"{route['route_number']}_{stop['stop_sequence']:03d}",
                'stop_name': stop['stop_name'],
                'fare_from_start': stop['fare_from_start']
            }
            for stop in route['stops']
        ])
        
        # Clean filename
        clean_route_num = re.sub(r'[^\w\-]', '_', route['route_number'])
        route_output_path = os.path.join(output_dir, f'route_{clean_route_num}.csv')
        route_df.to_csv(route_output_path, index=False, encoding='utf-8')
        print(f"Route CSV saved: {route_output_path}")
    
    return len(routes_data)

def main():
    """
    Main function to run the processor
    """
    input_file = "input.txt"  # Your Tesseract extracted text file
    output_directory = "output"
    
    print("Starting bus route processing...")
    print(f"Input file: {input_file}")
    print(f"Output directory: {output_directory}")
    print("-" * 50)
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        return
    
    # Process the text file
    routes_data = process_text_file(input_file)
    
    if routes_data:
        # Create CSV outputs
        route_count = create_csv_output(routes_data, output_directory)
        print("-" * 50)
        print(f"Processing completed!")
        print(f"Total routes processed: {route_count}")
        print(f"CSV files saved in '{output_directory}' folder")
    else:
        print("No valid route data found in the input file!")

if __name__ == "__main__":
    main()