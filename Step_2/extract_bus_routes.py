"""
Bus Route Table Extractor - TXT File Version
Extracts bus route data from text files and converts to CSV
Handles Sinhala text and various table formats
"""

import re
import csv
from pathlib import Path
import os

def extract_route_number(text):
    """Extract route number from header like 'මාර්ග අංක : 001'"""
    match = re.search(r'මාර්ග අංක\s*:\s*([\d-]+)', text)
    return match.group(1) if match else "Unknown"

def extract_route_name(text):
    """Extract route name like 'කොළඹ - මහනුවර'"""
    match = re.search(r'මාර්ග අංක\s*:\s*[\d-]+\s+(.+?)(?:\n|චරකාපොල)', text)
    if match:
        route_name = match.group(1).strip()
        return route_name
    return "Unknown"

def parse_table_data(text):
    """Parse bus stop table data from text"""
    routes = []
    lines = text.split('\n')
    
    for line in lines:
        # Skip header lines and empty lines
        if not line.strip() or 'ගාස්තු' in line or 'අවස්ථා' in line:
            continue
        
        # Skip lines with common header/footer text
        if any(word in line for word in ['ජාතික ගමනාගමන', 'කොමිෂන්', 'සභාව', 'උද්‍යාන පාර', 'ක්ෂණික ඇමතුම්']):
            continue
            
        # Pattern to match table rows: number distance separator location
        # Handles: 0 0.00] කොළඹ or 1 27.00| මාලිගාචත්ත
        pattern = r'(\d+)\s+(?:(\d+\.?\d*)\s*[|\]\}])?\s*(.+?)(?=\s+\d+\s+(?:\d+\.?\d*\s*[|\]\}]|$)|$)'
        
        matches = re.findall(pattern, line)
        
        for match in matches:
            stop_num = match[0]
            distance = match[1] if match[1] else ''
            location = match[2].strip()
            
            # Clean location name - remove extra spaces and numbers at start
            location = re.sub(r'^\d+\s+', '', location).strip()
            
            # Only add if location is valid and not empty
            if location and len(location) > 1:
                # Skip if location is just a number or separator
                if not re.match(r'^[\d\s|\]\}]+$', location):
                    routes.append({
                        'stop_number': stop_num,
                        'distance_km': distance,
                        'location': location
                    })
    
    return routes

def extract_routes_from_txt(txt_path):
    """Extract all bus route data from TXT file"""
    all_routes = []
    
    print(f"📖 Opening TXT file: {txt_path.name}")
    
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Split by page markers if they exist (e.g., "=== Page 1 ===")
        pages = re.split(r'===\s*Page\s+\d+\s*===', content)
        
        if len(pages) <= 1:
            # No page markers, treat as single page
            pages = [content]
        
        total_pages = len(pages)
        print(f"📄 Total pages/sections: {total_pages}")
        print("🔄 Processing...\n")
        
        for page_num, page_text in enumerate(pages):
            if not page_text.strip():
                continue
            
            if (page_num + 1) % 50 == 0:
                print(f"   Processed {page_num + 1}/{total_pages} pages...")
            
            # Extract route information
            route_number = extract_route_number(page_text)
            route_name = extract_route_name(page_text)
            
            # Parse table data
            stops = parse_table_data(page_text)
            
            # Add route metadata to each stop
            for stop in stops:
                stop['route_number'] = route_number
                stop['route_name'] = route_name
                stop['page_number'] = page_num + 1
                all_routes.append(stop)
        
        print(f"\n✅ Extraction complete!")
        print(f"📊 Total stops extracted: {len(all_routes)}")
        
    except Exception as e:
        print(f"❌ Error reading TXT file: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    return all_routes

def save_to_csv(routes, output_file):
    """Save extracted routes to CSV file"""
    if not routes:
        print("⚠️  No data to save!")
        return
    
    fieldnames = ['route_number', 'route_name', 'stop_number', 
                  'distance_km', 'location', 'page_number']
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(routes)
        
        print(f"✅ Data saved to: {output_file}")
        print(f"📊 Total records: {len(routes)}")
        
        # Show sample data
        print("\n📋 Sample data (first 5 records):")
        for i, route in enumerate(routes[:5]):
            print(f"   {i+1}. Route {route['route_number']}: "
                  f"Stop {route['stop_number']} - {route['location']} "
                  f"({route['distance_km']}km)")
        
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")

def find_txt_files(directory):
    """Find all TXT files in directory"""
    txt_files = list(Path(directory).glob('*.txt'))
    return txt_files

def main():
    """Main execution function"""
    print("=" * 70)
    print("🚌 BUS ROUTE TXT TO CSV CONVERTER")
    print("=" * 70)
    print()
    
    # Check for TXT files in input directory
    input_dir = Path('/app/input') if Path('/app/input').exists() else Path('input')
    output_dir = Path('/app/output') if Path('/app/output').exists() else Path('output')
    
    # Create directories if they don't exist
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    txt_files = find_txt_files(input_dir)
    
    if not txt_files:
        print(f"❌ No TXT files found in {input_dir}")
        print("   Please place your TXT file(s) in the 'input' folder")
        return
    
    print(f"📁 Found {len(txt_files)} TXT file(s):")
    for i, txt in enumerate(txt_files, 1):
        print(f"   {i}. {txt.name}")
    
    print()
    
    # Process all TXT files
    for txt_file in txt_files:
        print(f"\n{'='*70}")
        print(f"🔄 Processing: {txt_file.name}")
        print('='*70)
        
        all_routes = extract_routes_from_txt(txt_file)
        
        if all_routes:
            output_file = output_dir / f"{txt_file.stem}_routes.csv"
            save_to_csv(all_routes, str(output_file))
        else:
            print(f"⚠️  No data extracted from {txt_file.name}")
    
    print()
    print("=" * 70)
    print("✨ DONE! Check the 'output' folder for CSV files.")
    print("=" * 70)

if __name__ == "__main__":
    main()
