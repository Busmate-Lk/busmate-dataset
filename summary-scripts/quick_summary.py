#!/usr/bin/env python3
"""
Simple Bus Routes Summary Script
Answers specific questions about the dataset in a concise format.
"""

import re
from collections import defaultdict, Counter

def analyze_simple(file_path):
    """Simple analysis focusing on the requested metrics."""
    
    routes = []
    route_to_pages = defaultdict(list)
    main_route_counts = Counter()
    
    current_route = None
    current_route_data = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            
            if 'මාර්ග අංක :' in line:
                # Save previous route
                if current_route:
                    routes.append((current_route, current_route_data.copy()))
                    route_to_pages[current_route].append(current_route_data.copy())
                    main_route = re.match(r'^(\d{3})', current_route)
                    if main_route:
                        main_route_counts[main_route.group(1)] += 1
                
                # Start new route
                parts = line.split('මාර්ග අංක :')[1].strip().split(' ', 1)
                current_route = parts[0]
                current_route_data = []
                
            elif line and current_route and re.match(r'^\d+\s+[\d,]+\.\d+\s+', line):
                current_route_data.append(line)
    
    # Last route
    if current_route:
        routes.append((current_route, current_route_data.copy()))
        route_to_pages[current_route].append(current_route_data.copy())
        main_route = re.match(r'^(\d{3})', current_route)
        if main_route:
            main_route_counts[main_route.group(1)] += 1
    
    # Calculate page counts
    page_counts = {route: len(pages_list) for route, pages_list in route_to_pages.items()}
    
    return {
        'total_routes': len(routes),
        'unique_routes': len(set(route[0] for route in routes)),
        'total_pages': sum(page_counts.values()),
        'single_paged': sum(1 for count in page_counts.values() if count == 1),
        'double_paged': sum(1 for count in page_counts.values() if count == 2),
        'triple_paged': sum(1 for count in page_counts.values() if count == 3),
        'more_than_triple': sum(1 for count in page_counts.values() if count > 3),
        'main_route_counts': dict(main_route_counts.most_common())
    }

def main():
    file_path = "into-csv/all-converted-content-fixed-cleared.txt"
    
    print("🚌 Bus Routes Dataset - Quick Summary")
    print("=" * 50)
    
    results = analyze_simple(file_path)
    
    print(f"\n📊 ROUTE COUNTS")
    print(f"Total route entries: {results['total_routes']:,}")
    print(f"Unique routes: {results['unique_routes']:,}")
    
    print(f"\n📄 PAGE COUNTS")
    print(f"Total route pages: {results['total_pages']:,}")
    print(f"Single-paged routes: {results['single_paged']:,}")
    print(f"Double-paged routes: {results['double_paged']:,}")
    print(f"Triple-paged routes: {results['triple_paged']:,}")
    print(f"More than triple-paged: {results['more_than_triple']:,}")
    
    print(f"\n🚌 ROUTE CATEGORIES (by main number)")
    main_routes = results['main_route_counts']
    print(f"Total main categories: {len(main_routes)}")
    
    print(f"\nTop 10 categories by route count:")
    for i, (route, count) in enumerate(list(main_routes.items())[:10], 1):
        print(f"  {i:2d}. Route {route}: {count:,} variations")
    
    print(f"\nAll categories with counts:")
    for route in sorted(main_routes.keys()):
        count = main_routes[route]
        print(f"  Route {route}: {count}")

if __name__ == "__main__":
    main()