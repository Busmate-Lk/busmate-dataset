import re
import sys
import argparse
import os
from pathlib import Path

def preprocess_bus_routes(text):
    """
    Preprocess bus route data by extracting only relevant information:
    - Route number and description lines
    - Bus stop lines (with sequence number, distance, and stop name)
    - Route through lines
    """
    
    lines = text.split('\n')
    processed_lines = []
    
    # Patterns to identify relevant lines
    route_pattern = r'මාර්ග අංක\s*:\s*\d+'
    route_through_pattern = r'.*හරහා$'
    
    # Improved bus stop pattern to handle commas and various distance formats
    # Now matches: number + space + (number with optional commas).(number) + space + text
    bus_stop_pattern = r'^\d+\s+[\d,]+\.\d+\s+.+$'
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if it's a route number line
        if re.search(route_pattern, line):
            processed_lines.append(line)
            
        # Check if it's a "route through" line  
        elif re.search(route_through_pattern, line):
            processed_lines.append(line)
            
        # Check if it's a bus stop line (number, distance, name)
        elif re.search(bus_stop_pattern, line):
            processed_lines.append(line)
    
    return processed_lines

def process_file(input_file, output_file):
    """Process bus route data from input file and save to output file"""
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return None
    except Exception as e:
        print(f"Error reading input file: {e}")
        return None
    
    # Remove unwanted lines and keep only relevant data
    processed = preprocess_bus_routes(text)
    
    # Save processed data
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in processed:
                f.write(line + '\n')
        print(f"Successfully processed data saved to: {output_file}")
        print(f"Total lines kept: {len(processed)}")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        return None
    
    return processed

def main():
    # Get the script's directory to build relative paths
    script_dir = Path(__file__).parent.parent.parent  # Go up to dataset root
    
    # Default paths
    default_input = script_dir / "staging/step-1-extraction/unicode_converted_content.txt"
    default_output = script_dir / "staging/step-2-cleaning/cleaned_bus_routes.txt"
    
    parser = argparse.ArgumentParser(
        description='Clean and preprocess bus route data by removing unwanted text lines',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Default behavior (no arguments):
  Input:  {default_input}
  Output: {default_output}
        """
    )
    parser.add_argument('-i', '--input', 
                       help=f'Input file path containing bus route data (default: {default_input})')
    parser.add_argument('-o', '--output', 
                       help=f'Output file path for processed data (default: {default_output})')
    
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
    processed_data = process_file(input_file, output_file)
    
    if processed_data:
        print("\nSample of processed bus stop lines:")
        bus_stops = [line for line in processed_data if re.search(r'^\d+\s+[\d,]+\.\d+\s+.+$', line)]
        for i, line in enumerate(bus_stops[:15]):
            print(f"{i+1}: {line}")
        
        if len(bus_stops) > 15:
            print(f"... and {len(bus_stops) - 15} more bus stops")

if __name__ == "__main__":
    main()