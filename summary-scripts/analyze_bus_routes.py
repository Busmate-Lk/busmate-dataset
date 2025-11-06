#!/usr/bin/env python3
"""
Bus Routes Dataset Analysis Script

This script analyzes the bus routes dataset from 'into-csv/all-converted-content-fixed-cleared.txt'
and provides comprehensive statistics about route patterns, page counts, and categorical analysis.

Author: Assistant
Date: November 7, 2025
"""

import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set
import os

def extract_main_route_number(route_number: str) -> str:
    """
    Extract the main route number (e.g., '001', '002', '048') from complex route patterns.
    
    Examples:
    - '001' -> '001'
    - '001-001' -> '001'
    - '001-001/245' -> '001'
    - '048-013' -> '048'
    - '929-001' -> '929'
    """
    # Handle patterns like '001', '001-001', '001-001/245', etc.
    match = re.match(r'^(\d{3})', route_number)
    if match:
        return match.group(1)
    return route_number

def parse_route_line(line: str) -> Tuple[str, str]:
    """
    Parse a route line to extract route number and route description.
    
    Expected format: මාර්ග අංක : 001 කොළඹ - මහනුවර
    """
    if 'මාර්ග අංක :' in line:
        parts = line.split('මාර්ග අංක :')[1].strip()
        # Split by first space to separate route number from description
        route_parts = parts.split(' ', 1)
        if len(route_parts) >= 2:
            route_number = route_parts[0]
            route_description = route_parts[1]
            return route_number, route_description
        else:
            return route_parts[0], ""
    return "", ""

def analyze_bus_routes(file_path: str) -> Dict:
    """
    Analyze the bus routes dataset and return comprehensive statistics.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    # Data structures to store analysis results
    routes = []  # List of (route_number, description, pages_data)
    route_to_pages = defaultdict(list)  # route_number -> list of page data
    main_route_counts = Counter()  # main route number -> count
    unique_routes = set()  # unique route identifiers
    
    current_route = None
    current_route_data = []
    route_description = ""
    
    print("Reading and parsing dataset...")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    total_lines = len(lines)
    print(f"Total lines in dataset: {total_lines:,}")
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        # Check if this line contains a route header
        if 'මාර්ග අංක :' in line:
            # Save previous route if exists
            if current_route:
                routes.append((current_route, route_description, current_route_data.copy()))
                route_to_pages[current_route].append(current_route_data.copy())
                unique_routes.add(f"{current_route}:{route_description}")
                main_route = extract_main_route_number(current_route)
                main_route_counts[main_route] += 1
            
            # Start new route
            current_route, route_description = parse_route_line(line)
            current_route_data = []
            
        elif line and current_route:
            # This is route data (stops/stations)
            # Check if it's a numbered stop (starts with digit)
            if re.match(r'^\d+\s+[\d,]+\.\d+\s+', line):
                current_route_data.append(line)
    
    # Don't forget the last route
    if current_route:
        routes.append((current_route, route_description, current_route_data.copy()))
        route_to_pages[current_route].append(current_route_data.copy())
        unique_routes.add(f"{current_route}:{route_description}")
        main_route = extract_main_route_number(current_route)
        main_route_counts[main_route] += 1
    
    print("Analysis complete. Generating statistics...")
    
    # Calculate page statistics
    page_counts = {}
    for route_num, pages_list in route_to_pages.items():
        page_counts[route_num] = len(pages_list)
    
    # Categorize routes by page count
    single_paged = sum(1 for count in page_counts.values() if count == 1)
    double_paged = sum(1 for count in page_counts.values() if count == 2)
    triple_paged = sum(1 for count in page_counts.values() if count == 3)
    more_than_triple = sum(1 for count in page_counts.values() if count > 3)
    
    # Prepare results
    results = {
        'total_routes': len(routes),
        'unique_route_identifiers': len(unique_routes),
        'unique_route_numbers': len(set(route[0] for route in routes)),
        'total_route_pages': sum(page_counts.values()),
        'single_paged_routes': single_paged,
        'double_paged_routes': double_paged,
        'triple_paged_routes': triple_paged,
        'more_than_triple_paged_routes': more_than_triple,
        'main_route_counts': dict(main_route_counts.most_common()),
        'page_distribution': dict(Counter(page_counts.values())),
        'routes_by_page_count': page_counts,
        'sample_routes': routes[:10],  # First 10 routes for inspection
        'file_stats': {
            'total_lines': total_lines,
            'file_size_mb': os.path.getsize(file_path) / (1024 * 1024)
        }
    }
    
    return results

def print_analysis_report(results: Dict):
    """
    Print a comprehensive analysis report.
    """
    print("\n" + "=" * 80)
    print("BUS ROUTES DATASET ANALYSIS REPORT")
    print("=" * 80)
    
    print("\n📊 OVERALL STATISTICS")
    print("-" * 40)
    print(f"Total route entries found: {results['total_routes']:,}")
    print(f"Unique route identifiers: {results['unique_route_identifiers']:,}")
    print(f"Unique route numbers: {results['unique_route_numbers']:,}")
    print(f"Total route pages: {results['total_route_pages']:,}")
    
    print(f"\nFile Statistics:")
    print(f"  - Total lines in dataset: {results['file_stats']['total_lines']:,}")
    print(f"  - File size: {results['file_stats']['file_size_mb']:.2f} MB")
    
    print("\n📄 ROUTE PAGES ANALYSIS")
    print("-" * 40)
    print(f"Single-paged routes: {results['single_paged_routes']:,}")
    print(f"Double-paged routes: {results['double_paged_routes']:,}")
    print(f"Triple-paged routes: {results['triple_paged_routes']:,}")
    print(f"More than triple-paged routes: {results['more_than_triple_paged_routes']:,}")
    
    print("\n📈 PAGE COUNT DISTRIBUTION")
    print("-" * 40)
    page_dist = results['page_distribution']
    for page_count in sorted(page_dist.keys()):
        print(f"Routes with {page_count} page(s): {page_dist[page_count]:,}")
    
    print("\n🚌 MAIN ROUTE CATEGORIES (TOP 20)")
    print("-" * 40)
    main_routes = results['main_route_counts']
    top_20_routes = list(main_routes.items())[:20]
    
    for route_num, count in top_20_routes:
        print(f"Route {route_num}: {count:,} variations")
    
    if len(main_routes) > 20:
        remaining = sum(list(main_routes.values())[20:])
        print(f"... and {len(main_routes) - 20} more route categories with {remaining:,} total variations")
    
    print(f"\nTotal main route categories: {len(main_routes)}")
    
    print("\n🔍 DETAILED INSIGHTS")
    print("-" * 40)
    
    # Find routes with most pages
    max_pages = max(results['routes_by_page_count'].values()) if results['routes_by_page_count'] else 0
    routes_with_max_pages = [route for route, pages in results['routes_by_page_count'].items() if pages == max_pages]
    
    print(f"Maximum pages for a single route: {max_pages}")
    if routes_with_max_pages:
        print(f"Routes with maximum pages: {', '.join(routes_with_max_pages[:5])}")
        if len(routes_with_max_pages) > 5:
            print(f"  ... and {len(routes_with_max_pages) - 5} more routes")
    
    # Average pages per route
    if results['routes_by_page_count']:
        avg_pages = sum(results['routes_by_page_count'].values()) / len(results['routes_by_page_count'])
        print(f"Average pages per route: {avg_pages:.2f}")
    
    print("\n📋 SAMPLE ROUTES (First 10)")
    print("-" * 40)
    for i, (route_num, description, pages_data) in enumerate(results['sample_routes'], 1):
        page_count = results['routes_by_page_count'].get(route_num, 0)
        stops_count = len(pages_data)
        print(f"{i:2d}. Route {route_num}: {description}")
        print(f"    └─ {page_count} page(s), {stops_count} stops")

def main():
    """
    Main function to run the bus routes analysis.
    """
    # File path relative to the script location
    dataset_file = "into-csv/all-converted-content-fixed-cleared.txt"
    
    if not os.path.exists(dataset_file):
        print(f"❌ Error: Dataset file '{dataset_file}' not found!")
        print("Please ensure the file exists in the correct location.")
        return
    
    print("🚌 Bus Routes Dataset Analysis")
    print("=" * 50)
    
    try:
        # Perform analysis
        results = analyze_bus_routes(dataset_file)
        
        # Print comprehensive report
        print_analysis_report(results)
        
        print("\n" + "=" * 80)
        print("✅ Analysis completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()