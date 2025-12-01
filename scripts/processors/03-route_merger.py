import re
import sys
import argparse
import os
from pathlib import Path

def merge_route_sections(text):
    """
    Merge route sections that got split across multiple PDF pages.
    Routes with same header (ROUTE: line) should be merged into one.
    """
    
    lines = text.split('\n')
    merged_routes = []
    
    current_route_header = None
    current_route_through = None
    current_stops = []
    collecting_stops = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this is a new route header (ROUTE: line)
        if line.startswith('ROUTE:'):
            # Extract just the route info without "ROUTE: " prefix
            route_info = line[7:]  # Remove "ROUTE: "
            
            # If this is a different route than current one, save previous route
            if current_route_header and route_info != current_route_header:
                # Save the previous complete route
                merged_routes.append(f"ROUTE: {current_route_header}")
                if current_route_through:
                    merged_routes.append(f"ROUTE_THROUGH: {current_route_through}")
                else:
                    merged_routes.append("ROUTE_THROUGH: null")
                merged_routes.extend(current_stops)
                merged_routes.append("")  # Empty line between routes
                
                # Reset for new route
                current_stops = []
                current_route_through = None
            
            # Set or keep current route header
            current_route_header = route_info
            collecting_stops = True
            
        # Check if this is a ROUTE_THROUGH line
        elif line.startswith('ROUTE_THROUGH:'):
            # Only keep the first ROUTE_THROUGH for this route
            if not current_route_through:
                current_route_through = line[15:]  # Remove "ROUTE_THROUGH: "
            
        # Check if this is a bus stop line
        elif re.search(r'^\d+\s+[\d,]+\.\d+\s+.+$', line):
            if collecting_stops:
                current_stops.append(line)
    
    # Don't forget the last route
    if current_route_header:
        merged_routes.append(f"ROUTE: {current_route_header}")
        if current_route_through:
            merged_routes.append(f"ROUTE_THROUGH: {current_route_through}")
        else:
            merged_routes.append("ROUTE_THROUGH: null")
        merged_routes.extend(current_stops)
    
    return merged_routes

def process_file(input_file, output_file):
    """Merge route sections that were split across multiple PDF pages"""
    
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

def analyze_routes(merged_data):
    """Analyze routes to show merging results"""
    routes = []
    current_route = {}
    
    for line in merged_data:
        if line.startswith('ROUTE:'):
            if current_route:
                routes.append(current_route)
            current_route = {'header': line, 'stops': []}
        elif line.startswith('ROUTE_THROUGH:'):
            current_route['through'] = line
        elif re.search(r'^\d+\s+[\d,]+\.\d+\s+.+$', line):
            current_route['stops'].append(line)
    
    # Add the last route
    if current_route:
        routes.append(current_route)
    
    return routes

def main():
    # Get the script's directory to build relative paths
    script_dir = Path(__file__).parent.parent.parent  # Go up to dataset root
    
    # Default paths
    default_input = script_dir / "staging/step-3-formatting/formatted_bus_routes.txt"
    default_output = script_dir / "staging/step-4-route_merging/merged_bus_routes.txt"
    
    parser = argparse.ArgumentParser(
        description='Merge route sections that were split across multiple PDF pages',
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
        routes = analyze_routes(merged_data)
        print(f"Total complete routes after merging: {len(routes)}")
        
        print("\n=== Route Analysis ===")
        for i, route in enumerate(routes[:3]):  # Show first 3 routes as samples
            print(f"\nRoute {i+1}:")
            print(f"  Header: {route['header']}")
            print(f"  Through: {route.get('through', 'ROUTE_THROUGH: null')}")
            print(f"  Total stops: {len(route['stops'])}")
            
            # Show first 5 stops
            print(f"  First 5 stops:")
            for stop in route['stops'][:5]:
                print(f"    {stop}")
            
            # Show last 5 stops if route is long
            if len(route['stops']) > 10:
                print(f"  Last 5 stops:")
                for stop in route['stops'][-5:]:
                    print(f"    {stop}")
            
            # Check for stop numbering issues
            if route['stops']:
                first_stop = route['stops'][0]
                last_stop = route['stops'][-1]
                print(f"  Stop range: {first_stop.split()[0]} to {last_stop.split()[0]}")
        
        if len(routes) > 3:
            print(f"\n... and {len(routes) - 3} more routes")

if __name__ == "__main__":
    main()