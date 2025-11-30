import re
import sys
import argparse
import os
from pathlib import Path

def format_route_data(text):
    """
    Format bus route data with proper labels and ordering:
    - ROUTE: for route number lines (first)
    - ROUTE_THROUGH: for route through lines (second, or null if none)
    - Bus stops as normal (after)
    """
    
    lines = text.split('\n')
    formatted_lines = []
    
    # Patterns to identify relevant lines
    route_pattern = r'මාර්ග අංක\s*:\s*\d+'
    route_through_pattern = r'.*හරහා$'
    
    current_route = None
    current_route_through = None
    current_stops = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if it's a route number line
        if re.search(route_pattern, line):
            # If we have a previous route to process, save it first
            if current_route:
                # Add the route line
                formatted_lines.append(f"ROUTE: {current_route}")
                
                # Add route through line (or null)
                if current_route_through:
                    formatted_lines.append(f"ROUTE_THROUGH: {current_route_through}")
                else:
                    formatted_lines.append("ROUTE_THROUGH: null")
                
                # Add all collected stops
                formatted_lines.extend(current_stops)
                formatted_lines.append("")  # Add empty line between routes
            
            # Start new route
            current_route = line
            current_route_through = None
            current_stops = []
            
        # Check if it's a "route through" line
        elif re.search(route_through_pattern, line):
            current_route_through = line
            
        # Bus stop line
        elif re.search(r'^\d+\s+[\d,]+\.\d+\s+.+$', line):
            current_stops.append(line)
    
    # Don't forget the last route
    if current_route:
        formatted_lines.append(f"ROUTE: {current_route}")
        
        if current_route_through:
            formatted_lines.append(f"ROUTE_THROUGH: {current_route_through}")
        else:
            formatted_lines.append("ROUTE_THROUGH: null")
        
        formatted_lines.extend(current_stops)
    
    return formatted_lines

def process_file(input_file, output_file):
    """Process cleaned bus route data and format it with proper labels and ordering"""
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return None
    except Exception as e:
        print(f"Error reading input file: {e}")
        return None
    
    # Format the route data with labels and proper ordering
    formatted_data = format_route_data(text)
    
    # Save formatted data
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in formatted_data:
                f.write(line + '\n')
        print(f"Successfully formatted data saved to: {output_file}")
        print(f"Total formatted lines: {len(formatted_data)}")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        return None
    
    return formatted_data

def main():
    # Get the script's directory to build relative paths
    script_dir = Path(__file__).parent.parent.parent  # Go up to dataset root
    
    # Default paths
    default_input = script_dir / "staging/step-2-cleaning/cleaned_bus_routes.txt"
    default_output = script_dir / "staging/step-3-formatting/formatted_bus_routes.txt"
    
    parser = argparse.ArgumentParser(
        description='Format bus route data with proper ROUTE and ROUTE_THROUGH ordering',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Default behavior (no arguments):
  Input:  {default_input}
  Output: {default_output}
        """
    )
    parser.add_argument('-i', '--input', 
                       help=f'Input file path containing cleaned bus route data (default: {default_input})')
    parser.add_argument('-o', '--output', 
                       help=f'Output file path for formatted data (default: {default_output})')
    
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
    formatted_data = process_file(input_file, output_file)
    
    if formatted_data:
        print("\nSample of formatted data:")
        for i, line in enumerate(formatted_data[:25]):
            if line:  # Only show non-empty lines
                print(f"{i+1}: {line}")
        
        if len(formatted_data) > 25:
            print(f"... and {len(formatted_data) - 25} more lines")

if __name__ == "__main__":
    main()