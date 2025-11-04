"""
PDF Bus Route Table Extractor
Extracts bus route data from multiple pages and converts to CSV
Handles Sinhala text and various table formats

SETUP INSTRUCTIONS FOR KALI LINUX:
1. Create virtual environment: python3 -m venv bus_env
2. Activate it: source bus_env/bin/activate
3. Install PyPDF2: pip install PyPDF2
4. Run this script: python extract_bus_routes.py
"""

import re
import csv
import sys
from pathlib import Path

# Try importing PyPDF2
try:
    import PyPDF2
except ImportError:
    print("❌ Error: PyPDF2 is not installed!")
    print("\n📦 Installation instructions:")
    print("   1. Create virtual environment:")
    print("      python3 -m venv bus_env")
    print("\n   2. Activate it:")
    print("      source bus_env/bin/activate")
    print("\n   3. Install PyPDF2:")
    print("      pip install PyPDF2")
    print("\n   4. Run this script again:")
    print("      python extract_bus_routes.py")
    sys.exit(1)

def extract_route_number(text):
    """Extract route number from header like 'මාර්ග අංක : 001'"""
    match = re.search(r'මාර්ග අංක\s*:\s*([\d-]+)', text)
    return match.group(1) if match else "Unknown"

def extract_route_name(text):
    """Extract route name like 'කොළඹ - මහනුවර'"""
    # Look for pattern after route number
    match = re.search(r'මාර්ග අංක\s*:\s*[\d-]+\s+(.+?)(?:\n|චරකාපොල)', text)
    if match:
        route_name = match.group(1).strip()
        return route_name
    return "Unknown"

def parse_table_data(text):
    """
    Parse bus stop table data from text
    Handles multiple formats and missing data
    """
    routes = []

    # Split into lines
    lines = text.split('\n')

    for line in lines:
        # Skip header lines and empty lines
        if not line.strip() or 'ගාස්තු' in line or 'අවස්ථා' in line:
            continue

        # Pattern to match table rows: number distance separator location
        # Handles: 0 0.00] කොළඹ or 1 27.00| මාලිගාචත්ත
        pattern = r'(\d+)\s+(?:(\d+\.?\d*)\s*[|\]\}])?\s*(.+?)(?=\s+\d+\s+\d+\.?\d*[|\]\}]|$)'

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

def extract_all_routes_from_pdf(pdf_path):
    """
    Extract all bus route data from PDF
    Returns list of dictionaries with route info
    """
    all_routes = []

    print(f"📖 Opening PDF: {pdf_path}")

    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)

            print(f"📄 Total pages: {total_pages}")
            print("🔄 Processing pages...\n")

            for page_num in range(total_pages):
                # Show progress every 50 pages
                if (page_num + 1) % 50 == 0:
                    print(f"   Processed {page_num + 1}/{total_pages} pages...")

                page = pdf_reader.pages[page_num]
                text = page.extract_text()

                # Extract route information
                route_number = extract_route_number(text)
                route_name = extract_route_name(text)

                # Parse table data
                stops = parse_table_data(text)

                # Add route metadata to each stop
                for stop in stops:
                    stop['route_number'] = route_number
                    stop['route_name'] = route_name
                    stop['page_number'] = page_num + 1
                    all_routes.append(stop)

            print(f"\n✅ Extraction complete!")
            print(f"📊 Total stops extracted: {len(all_routes)}")

    except Exception as e:
        print(f"❌ Error reading PDF: {e}")
        return []

    return all_routes

def save_to_csv(routes, output_file='bus_routes_all.csv'):
    """
    Save extracted routes to CSV file
    """
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

def main():
    """
    Main execution function
    """
    print("=" * 70)
    print("🚌 BUS ROUTE PDF TO CSV CONVERTER")
    print("=" * 70)
    print()

    # Get PDF file path from user
    pdf_path = input("📁 Enter PDF file path (or press Enter for 'bus_routes.pdf'): ").strip()

    if not pdf_path:
        pdf_path = 'bus_routes.pdf'

    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"❌ Error: File '{pdf_path}' not found!")
        return

    # Extract data
    print()
    all_routes = extract_all_routes_from_pdf(pdf_path)

    if not all_routes:
        print("⚠️  No route data extracted. Please check the PDF format.")
        return

    # Save to CSV
    print()
    output_file = input("💾 Enter output CSV filename (or press Enter for 'bus_routes_all.csv'): ").strip()

    if not output_file:
        output_file = 'bus_routes_all.csv'

    if not output_file.endswith('.csv'):
        output_file += '.csv'

    print()
    save_to_csv(all_routes, output_file)

    print()
    print("=" * 70)
    print("✨ DONE! You can now open the CSV file in Excel or any spreadsheet app.")
    print("=" * 70)

if __name__ == "__main__":
    main()
