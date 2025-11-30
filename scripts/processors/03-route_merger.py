import re
import sys
import argparse
import os
from pathlib import Path

def merge_route_sections(text):
    """
    Merge route sections that got split across PDF pages.
    Routes are identified by the pattern where each route starts with:
    - Stop order: 0
    - Distance: 0.00
    """
    
    lines = text.split('\n')
    merged_routes = []
    
    current_route = []
    collecting_stops = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a new route header (ROUTE: line)
        if line.startswith('ROUTE:'):
            # If we were collecting stops from previous route, save it first
            if current_route and collecting_stops:
                merged_routes.extend(current_route)
                merged_routes.append("")  # Add empty line between routes
            
            # Start new route collection
            current_route = [line]
            collecting_stops = False
            
        # Check if this is a ROUTE_THROUGH line
        elif line.startswith('ROUTE_THROUGH:'):
            current_route.append(line)
            
        # Check if this is a bus stop line
        elif re.search(r'^\d+\s+[\d,]+\.\d+\s+.+$', line):
            # Check if this is the beginning of stops (stop 0, distance 0.00)
            if re.search(r'^0\s+0\.00\s+', line):
                # If we already have stops in current_route, this is a new route
                if collecting_stops:
                    # Save the current route and start new one
                    merged_routes.extend(current_route)
                    merged_routes.append("")
                    # Keep only the route header lines (ROUTE and ROUTE_THROUGH)
                    route_header = [l for l in current_route if l.startswith(('ROUTE:', 'ROUTE_THROUGH:'))]
                    current_route = route_header
                
                collecting_stops = True
            
            current_route.append(line)
    
    # Don't forget the last route
    if current_route:
        merged_routes.extend(current_route)
    
    return merged_routes

def process_file(input_file, output_file):
    """Merge route sections that were split across PDF pages"""
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return None
    except Exception as e:
        print(f"Error reading input file: {e}")
        return None
    
    # Merge route sections
    merged_data = merge_route_sections(text)
    
    # Save merged data
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for line in merged_data:
                f.write(line + '\n')
        print(f"Successfully merged route data saved to: {output_file}")
        print(f"Total lines after merging: {len(merged_data)}")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        return None
    
    return merged_data

def count_routes(merged_data):
    """Count how many complete routes we have after merging"""
    route_count = 0
    for line in merged_data:
        if line.startswith('ROUTE:'):
            route_count += 1
    return route_count

def main():
    # Get the script's directory to build relative paths
    script_dir = Path(__file__).parent.parent.parent  # Go up to dataset root
    
    # Default paths
    default_input = script_dir / "staging/step-3-formatting/formatted_bus_routes.txt"
    default_output = script_dir / "staging/step-4-route_merging/merged_bus_routes.txt"
    
    parser = argparse.ArgumentParser(
        description='Merge route sections that were split across PDF pages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Default behavior (no arguments):
  Input:  {default_input}
  Output: {default_output}
        """
    )
    parser.add_argument('-i', '--input', 
                       help=f'Input file path containing formatted bus route data (default: {default_input})')
    parser.add_argument('-o', '--output', 
                       help=f'Output file path for merged route data (default: {default_output})')
    
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
    merged_data = process_file(input_file, output_file)
    
    if merged_data:
        route_count = count_routes(merged_data)
        print(f"Total complete routes after merging: {route_count}")
        
        print("\nSample of merged routes:")
        route_samples = []
        current_route = []
        
        for line in merged_data:
            if line.startswith('ROUTE:'):
                if current_route:
                    route_samples.append(current_route)
                    if len(route_samples) >= 2:  # Show 2 sample routes
                        break
                current_route = [line]
            elif line:
                current_route.append(line)
        
        # Add the last route if we have samples to show
        if current_route and len(route_samples) < 2:
            route_samples.append(current_route)
        
        for i, route in enumerate(route_samples):
            print(f"\n--- Sample Route {i+1} ---")
            for j, line in enumerate(route[:15]):  # Show first 15 lines of each route
                print(f"  {line}")
            if len(route) > 15:
                print(f"  ... and {len(route) - 15} more stops")

if __name__ == "__main__":
    main()