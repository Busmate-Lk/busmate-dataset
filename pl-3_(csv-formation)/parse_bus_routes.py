#!/usr/bin/env python3
"""
Bus Route Data Parser
Converts bus route data from text format to structured CSV format.

This script parses bus route data from a text file and converts it to CSV format
with columns for route information and stop details.
"""

import csv
import re
import os
from typing import List, Dict, Tuple, Optional

class BusRouteParser:
    def __init__(self, input_file: str, output_file: str):
        """
        Initialize the parser with input and output file paths.
        
        Args:
            input_file: Path to the input text file
            output_file: Path to the output CSV file
        """
        self.input_file = input_file
        self.output_file = output_file
        self.routes_data = []
        
    def parse_route_data(self) -> List[Dict]:
        """
        Parse the bus route data from the input file.
        
        Returns:
            List of dictionaries containing route and stop information
        """
        routes = []
        
        try:
            with open(self.input_file, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                
            current_route = None
            current_route_through = None
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip empty lines
                if not line:
                    i += 1
                    continue
                
                # Check if line contains "හරහා" (route through)
                if line.endswith('හරහා'):
                    # Save previous route before starting new section
                    if current_route and current_route['stops']:
                        routes.append(current_route)
                        current_route = None
                    
                    current_route_through = line.replace('හරහා', '').strip()
                    i += 1
                    continue
                
                # Check if line contains route number info
                if line.startswith('මාර්ග අංක :'):
                    # Save previous route before starting new route
                    if current_route and current_route['stops']:
                        routes.append(current_route)
                    
                    # Extract route number and route name
                    route_info = line.replace('මාර්ග අංක :', '').strip()
                    route_parts = route_info.split(' ', 1)
                    
                    if len(route_parts) >= 2:
                        route_number = route_parts[0]
                        route_name = route_parts[1]
                    else:
                        route_number = route_info
                        route_name = ""
                    
                    current_route = {
                        'route_number': route_number,
                        'route_name': route_name,
                        'route_through': current_route_through or "",
                        'stops': []
                    }
                    i += 1
                    continue
                
                # Check if line contains stop information (number fare stop_name)
                if current_route is not None:
                    stop_match = re.match(r'^(\d+)\s+(\d+\.?\d*)\s+(.+)$', line)
                    if stop_match:
                        stop_sequence = int(stop_match.group(1))
                        fare = float(stop_match.group(2))
                        stop_name = stop_match.group(3).strip()
                        
                        current_route['stops'].append({
                            'stop_sequence': stop_sequence,
                            'stop_name': stop_name,
                            'fare_from_start': fare
                        })
                        i += 1
                        continue
                
                # For any other line, just continue to next line
                i += 1
            
            # Don't forget the last route if file doesn't end with empty lines
            if current_route and current_route['stops']:
                routes.append(current_route)
                
        except FileNotFoundError:
            print(f"Error: Input file '{self.input_file}' not found.")
            return []
        except Exception as e:
            print(f"Error reading file: {e}")
            return []
        
        return routes
    
    def calculate_fare_differences(self, stops: List[Dict]) -> List[Dict]:
        """
        Calculate fare differences between consecutive stops.
        
        Args:
            stops: List of stop dictionaries
            
        Returns:
            List of stops with additional fare information
        """
        enhanced_stops = []
        
        for i, stop in enumerate(stops):
            enhanced_stop = stop.copy()
            
            # Calculate fare from previous stop
            if i == 0:
                enhanced_stop['fare_from_previous'] = stop['fare_from_start']
            else:
                prev_fare = stops[i-1]['fare_from_start']
                enhanced_stop['fare_from_previous'] = stop['fare_from_start'] - prev_fare
            
            enhanced_stops.append(enhanced_stop)
        
        return enhanced_stops
    
    def write_to_csv(self, routes: List[Dict]) -> bool:
        """
        Write the parsed route data to CSV file.
        
        Args:
            routes: List of route dictionaries
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
            
            with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'route_number',
                    'route_name', 
                    'route_through',
                    'stop_sequence',
                    'stop_name',
                    'fare_from_start',
                    'fare_from_previous'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for route in routes:
                    enhanced_stops = self.calculate_fare_differences(route['stops'])
                    
                    for stop in enhanced_stops:
                        row = {
                            'route_number': route['route_number'],
                            'route_name': route['route_name'],
                            'route_through': route['route_through'],
                            'stop_sequence': stop['stop_sequence'],
                            'stop_name': stop['stop_name'],
                            'fare_from_start': f"{stop['fare_from_start']:.2f}",
                            'fare_from_previous': f"{stop['fare_from_previous']:.2f}"
                        }
                        writer.writerow(row)
            
            return True
            
        except Exception as e:
            print(f"Error writing CSV file: {e}")
            return False
    
    def generate_summary_stats(self, routes: List[Dict]) -> Dict:
        """
        Generate summary statistics about the parsed data.
        
        Args:
            routes: List of route dictionaries
            
        Returns:
            Dictionary containing summary statistics
        """
        if not routes:
            return {}
        
        total_routes = len(routes)
        total_stops = sum(len(route['stops']) for route in routes)
        
        # Find route with most stops
        max_stops_route = max(routes, key=lambda r: len(r['stops']))
        
        # Calculate average stops per route
        avg_stops = total_stops / total_routes if total_routes > 0 else 0
        
        # Find unique route through locations
        route_throughs = set(route['route_through'] for route in routes if route['route_through'])
        
        return {
            'total_routes': total_routes,
            'total_stops': total_stops,
            'average_stops_per_route': round(avg_stops, 2),
            'max_stops_in_route': len(max_stops_route['stops']),
            'max_stops_route_number': max_stops_route['route_number'],
            'unique_route_through_locations': len(route_throughs),
            'route_through_locations': sorted(list(route_throughs))
        }
    
    def process(self) -> bool:
        """
        Main processing function to parse and convert data.
        
        Returns:
            True if processing successful, False otherwise
        """
        print("Starting bus route data processing...")
        print(f"Input file: {self.input_file}")
        print(f"Output file: {self.output_file}")
        print("-" * 50)
        
        # Parse the data
        print("Parsing route data...")
        routes = self.parse_route_data()
        
        if not routes:
            print("No route data found or error in parsing.")
            return False
        
        # Generate statistics
        stats = self.generate_summary_stats(routes)
        
        print(f"Successfully parsed {stats['total_routes']} routes with {stats['total_stops']} total stops")
        print(f"Average stops per route: {stats['average_stops_per_route']}")
        print(f"Route with most stops: {stats['max_stops_route_number']} ({stats['max_stops_in_route']} stops)")
        print(f"Unique route-through locations: {stats['unique_route_through_locations']}")
        
        # Write to CSV
        print("\nWriting data to CSV...")
        success = self.write_to_csv(routes)
        
        if success:
            print(f"Successfully created CSV file: {self.output_file}")
            print("CSV Structure:")
            print("- route_number: Bus route number (e.g., 001, 001-001)")
            print("- route_name: Route name/description")
            print("- route_through: Location route passes through")
            print("- stop_sequence: Sequential stop number")
            print("- stop_name: Name of the bus stop")
            print("- fare_from_start: Total fare from starting point")
            print("- fare_from_previous: Fare from previous stop")
            return True
        else:
            print("Failed to create CSV file.")
            return False

def main():
    """Main function to run the bus route parser."""
    
    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, "all-converted-content-fixed-cleared.txt")
    output_file = os.path.join(script_dir, "bus_routes_structured.csv")
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        print("Please make sure the file 'all-converted-content-fixed-cleared.txt' exists in the same directory as this script.")
        return
    
    # Create parser and process data
    parser = BusRouteParser(input_file, output_file)
    success = parser.process()
    
    if success:
        print("\n" + "="*50)
        print("PROCESSING COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"Output file created: {output_file}")
    else:
        print("\n" + "="*50)
        print("PROCESSING FAILED!")
        print("="*50)

if __name__ == "__main__":
    main()