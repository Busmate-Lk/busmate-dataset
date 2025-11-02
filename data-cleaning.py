import re
import pandas as pd

def extract_route_data(text):
    """
    Extract route information and stops from raw text
    """
    # Extract route number and name
    route_match = re.search(r'මාර්ග අංක\s*:\s*([^\n]+)', text)
    route_info = route_match.group(1).strip() if route_match else "Unknown"
    
    # Extract route description (Colombo - Destination)
    route_desc_match = re.search(r'මාර්ග අංක[^\n]+\n([^\n]+)', text)
    route_desc = route_desc_match.group(1).strip() if route_desc_match else ""
    
    # Extract stops with fares - pattern: number fare stop_name
    stops = []
    stop_pattern = r'(\d+)\s+([\d.]+)\]\s*([^\n]+?)(?=\n\d|\n\n|$)'
    
    for match in re.finditer(stop_pattern, text):
        stop_num = int(match.group(1))
        fare = float(match.group(2))
        stop_name = match.group(3).strip()
        
        # Clean up common OCR errors
        stop_name = clean_stop_name(stop_name)
        
        stops.append({
            'stop_sequence': stop_num,
            'stop_name': stop_name,
            'fare': fare
        })
    
    return {
        'route_number': route_info,
        'route_description': route_desc,
        'stops': stops
    }

def clean_stop_name(name):
    """
    Clean common OCR errors in Sinhala stop names
    """
    corrections = {
        'චිශ්ච චිදා9ාලය': 'විද්‍යාලය',
        'චිදා9ාලය': 'විද්‍යාලය',
        'හංදිය': 'හන්දිය',
        'හංදියට': 'හන්දියට',
        'Bae': 'බදුල්ල',  # Common OCR error
        'ට්‍රැක්මෙ?': 'ට්‍රැක්මෙන්',
        'දෝොණිය': 'දෝණිය'
    }
    
    for error, correction in corrections.items():
        name = name.replace(error, correction)
    
    return name

def process_pdf_text(pages_text):
    """
    Process all pages and return structured data
    """
    all_routes = []
    
    # Split by pages and process each
    pages = pages_text.split("=== Page")
    for page in pages[1:]:  # Skip first empty split
        route_data = extract_route_data(page)
        all_routes.append(route_data)
    
    return all_routes

def create_csv_output(routes_data):
    """
    Convert structured data to CSV format
    """
    csv_data = []
    
    for route in routes_data:
        for stop in route['stops']:
            csv_data.append({
                'route_number': route['route_number'],
                'route_name': route['route_description'],
                'stop_sequence': stop['stop_sequence'],
                'stop_id': f"{route['route_number']}_{stop['stop_sequence']}",
                'stop_name': stop['stop_name'],
                'fare_from_start': stop['fare']
            })
    
    return pd.DataFrame(csv_data)

# Usage example:
# df = create_csv_output(process_pdf_text(your_raw_text))
# df.to_csv('bus_routes_sri_lanka.csv', index=False, encoding='utf-8')