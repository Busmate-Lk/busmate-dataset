import re
import csv
import sys
import argparse
import os
from pathlib import Path

def extract_route_info(route_line):
    """Extract route number and name from ROUTE line"""
    # Example: "ROUTE: මාර්ග අංක : 001 කොළඹ - මහනුවර"
    match = re.search(r'මාර්ග අංක\s*:\s*([^\s]+)\s+(.+)', route_line)
    if match:
        route_number = match.group(1).strip()
        route_name = match.group(2).strip()
        return route_number, route_name
    return None, None

def parse_stop_line(stop_line):
    """Parse stop line into sequence, fare, and name"""
    # Example: "0 0.00 කොළඹ" or "159 1,003.00 රොටරිගම"
    match = re.match(r'^(\d+)\s+([\d,]+\.\d+)\s+(.+)$', stop_line)
    if match:
        sequence = int(match.group(1))
        fare = float(match.group(2).replace(',', ''))
        name = match.group(3).strip()
        return sequence, fare, name
    return None, None, None

def convert_to_csv(text):
    """
    Convert structured route data to CSV format with columns:
    - route_number, route_name, route_through, stop_sequence, stop_name, fare_from_start
    """
    
    lines = text.split('\n')
    csv_data = []
    
    current_route_number = None
    current_route_name = None
    current_route_through = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Process ROUTE line
        if line.startswith('ROUTE:'):
            route_line = line.replace('ROUTE: ', '')
            current_route_number, current_route_name = extract_route_info(route_line)
            
        # Process ROUTE_THROUGH line
        elif line.startswith('ROUTE_THROUGH:'):
            route_through = line.replace('ROUTE_THROUGH: ', '')
            if route_through != 'null':
                current_route_through = route_through
            else:
                current_route_through = None
                
        # Process bus stop line
        elif re.search(r'^\d+\s+[\d,]+\.\d+\s+.+$', line):
            if current_route_number and current_route_name:
                sequence, fare, stop_name = parse_stop_line(line)
                if sequence is not None:
                    csv_data.append({
                        'route_number': current_route_number,
                        'route_name': current_route_name,
                        'route_through': current_route_through if current_route_through else '',
                        'stop_sequence': sequence,
                        'stop_name': stop_name,
                        'fare_from_start': fare
                    })
    
    return csv_data

def process_file(input_file, output_file):
    """Convert structured route data to CSV format"""
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return None
    except Exception as e:
        print(f"Error reading input file: {e}")
        return None
    
    # Convert to CSV data
    csv_data = convert_to_csv(text)
    
    # Save as CSV file
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            if csv_data:
                fieldnames = ['route_number', 'route_name', 'route_through', 'stop_sequence', 'stop_name', 'fare_from_start']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                
                writer.writeheader()
                writer.writerows(csv_data)
                
        print(f"Successfully converted to CSV: {output_file}")
        print(f"Total records: {len(csv_data)}")
        
        # Show some statistics
        unique_routes = set((item['route_number'], item['route_name']) for item in csv_data)
        print(f"Unique routes: {len(unique_routes)}")
        
    except Exception as e:
        print(f"Error writing CSV file: {e}")
        return None
    
    return csv_data

def main():
    # Get the script's directory to build relative paths
    script_dir = Path(__file__).parent.parent.parent  # Go up to dataset root
    
    # Default paths
    default_input = script_dir / "staging/step-4-route_merging/merged_bus_routes.txt"
    default_output = script_dir / "staging/step-5-basic_csv/bus_routes.csv"
    
    parser = argparse.ArgumentParser(
        description='Convert structured bus route data to CSV format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Default behavior (no arguments):
  Input:  {default_input}
  Output: {default_output}
        """
    )
    parser.add_argument('-i', '--input', 
                       help=f'Input file path containing merged bus route data (default: {default_input})')
    parser.add_argument('-o', '--output', 
                       help=f'Output CSV file path (default: {default_output})')
    
    args = parser.parse_args()
    
    # Use provided arguments or defaults
    input_file = args.input if args.input else str(default_input)
    output_file = args.output if args.output else str(default_output)
    
    # Ensure output directory exists
    output_dir = Path(output_file).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    
    # Process the file
    csv_data = process_file(input_file, output_file)
    
    if csv_data:
        print("\nSample of CSV data (first 10 records):")
        print("route_number,route_name,route_through,stop_sequence,stop_name,fare_from_start")
        for i, record in enumerate(csv_data[:10]):
            print(f"{record['route_number']},{record['route_name']},{record['route_through']},{record['stop_sequence']},{record['stop_name']},{record['fare_from_start']}")

if __name__ == "__main__":
    main()