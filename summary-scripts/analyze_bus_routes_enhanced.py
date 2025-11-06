#!/usr/bin/env python3
"""
Enhanced Bus Routes Dataset Analysis Script

This enhanced version provides additional detailed analysis including:
- Route complexity analysis
- Geographic patterns
- Stop count analysis
- Route variation patterns

Author: Assistant
Date: November 7, 2025
"""

import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Set
import os
import json

def extract_main_route_number(route_number: str) -> str:
    """Extract the main route number from complex route patterns."""
    match = re.match(r'^(\d{3})', route_number)
    if match:
        return match.group(1)
    return route_number

def parse_route_line(line: str) -> Tuple[str, str]:
    """Parse a route line to extract route number and route description."""
    if 'මාර්ග අංක :' in line:
        parts = line.split('මාර්ග අංක :')[1].strip()
        route_parts = parts.split(' ', 1)
        if len(route_parts) >= 2:
            route_number = route_parts[0]
            route_description = route_parts[1]
            return route_number, route_description
        else:
            return route_parts[0], ""
    return "", ""

def extract_cities_from_description(description: str) -> List[str]:
    """Extract city names from route description."""
    # Split by common separators and clean
    cities = []
    if ' - ' in description:
        parts = description.split(' - ')
        for part in parts:
            # Remove repeated words and clean
            cleaned = re.sub(r'\b(\w+)\s+\1\b', r'\1', part.strip())
            if cleaned:
                cities.append(cleaned)
    return cities

def analyze_bus_routes_enhanced(file_path: str) -> Dict:
    """Enhanced analysis of the bus routes dataset."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    # Data structures
    routes = []
    route_to_pages = defaultdict(list)
    main_route_counts = Counter()
    unique_routes = set()
    stop_counts = []
    city_frequency = Counter()
    route_complexity = {}  # route -> complexity score
    
    current_route = None
    current_route_data = []
    route_description = ""
    
    print("Reading and parsing dataset...")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    total_lines = len(lines)
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        
        if 'මාර්ග අංක :' in line:
            # Save previous route
            if current_route:
                routes.append((current_route, route_description, current_route_data.copy()))
                route_to_pages[current_route].append(current_route_data.copy())
                unique_routes.add(f"{current_route}:{route_description}")
                main_route = extract_main_route_number(current_route)
                main_route_counts[main_route] += 1
                
                # Analyze stops
                stop_counts.append(len(current_route_data))
                
                # Analyze cities
                cities = extract_cities_from_description(route_description)
                for city in cities:
                    city_frequency[city] += 1
                
                # Calculate complexity (based on route number patterns)
                complexity = len(current_route.split('-')) + len(current_route.split('/'))
                route_complexity[current_route] = complexity
            
            # Start new route
            current_route, route_description = parse_route_line(line)
            current_route_data = []
            
        elif line and current_route:
            if re.match(r'^\d+\s+[\d,]+\.\d+\s+', line):
                current_route_data.append(line)
    
    # Don't forget the last route
    if current_route:
        routes.append((current_route, route_description, current_route_data.copy()))
        route_to_pages[current_route].append(current_route_data.copy())
        unique_routes.add(f"{current_route}:{route_description}")
        main_route = extract_main_route_number(current_route)
        main_route_counts[main_route] += 1
        stop_counts.append(len(current_route_data))
        cities = extract_cities_from_description(route_description)
        for city in cities:
            city_frequency[city] += 1
        complexity = len(current_route.split('-')) + len(current_route.split('/'))
        route_complexity[current_route] = complexity
    
    # Calculate statistics
    page_counts = {}
    for route_num, pages_list in route_to_pages.items():
        page_counts[route_num] = len(pages_list)
    
    # Page categorization
    single_paged = sum(1 for count in page_counts.values() if count == 1)
    double_paged = sum(1 for count in page_counts.values() if count == 2)
    triple_paged = sum(1 for count in page_counts.values() if count == 3)
    more_than_triple = sum(1 for count in page_counts.values() if count > 3)
    
    # Stop statistics
    if stop_counts:
        avg_stops = sum(stop_counts) / len(stop_counts)
        min_stops = min(stop_counts)
        max_stops = max(stop_counts)
        median_stops = sorted(stop_counts)[len(stop_counts) // 2]
    else:
        avg_stops = min_stops = max_stops = median_stops = 0
    
    # Route complexity analysis
    complexity_distribution = Counter(route_complexity.values())
    simple_routes = sum(1 for c in route_complexity.values() if c <= 2)
    complex_routes = sum(1 for c in route_complexity.values() if c > 3)
    
    results = {
        'basic_stats': {
            'total_routes': len(routes),
            'unique_route_identifiers': len(unique_routes),
            'unique_route_numbers': len(set(route[0] for route in routes)),
            'total_route_pages': sum(page_counts.values()),
        },
        'page_analysis': {
            'single_paged_routes': single_paged,
            'double_paged_routes': double_paged,
            'triple_paged_routes': triple_paged,
            'more_than_triple_paged_routes': more_than_triple,
            'page_distribution': dict(Counter(page_counts.values())),
            'max_pages': max(page_counts.values()) if page_counts else 0,
            'avg_pages': sum(page_counts.values()) / len(page_counts) if page_counts else 0,
        },
        'stop_analysis': {
            'total_stops': sum(stop_counts),
            'avg_stops_per_route': avg_stops,
            'min_stops': min_stops,
            'max_stops': max_stops,
            'median_stops': median_stops,
            'stop_count_distribution': dict(Counter(stop_counts)),
        },
        'route_categories': {
            'main_route_counts': dict(main_route_counts.most_common()),
            'total_categories': len(main_route_counts),
        },
        'complexity_analysis': {
            'simple_routes': simple_routes,
            'complex_routes': complex_routes,
            'complexity_distribution': dict(complexity_distribution),
            'most_complex_routes': sorted(route_complexity.items(), key=lambda x: x[1], reverse=True)[:10],
        },
        'geographic_analysis': {
            'top_cities': dict(city_frequency.most_common(20)),
            'total_unique_cities': len(city_frequency),
        },
        'detailed_data': {
            'routes_by_page_count': page_counts,
            'sample_routes': routes[:20],
        },
        'file_stats': {
            'total_lines': total_lines,
            'file_size_mb': os.path.getsize(file_path) / (1024 * 1024)
        }
    }
    
    return results

def print_enhanced_report(results: Dict):
    """Print enhanced analysis report."""
    print("\n" + "=" * 90)
    print("🚌 ENHANCED BUS ROUTES DATASET ANALYSIS REPORT")
    print("=" * 90)
    
    # Basic Statistics
    basic = results['basic_stats']
    print("\n📊 OVERALL STATISTICS")
    print("-" * 50)
    print(f"Total route entries: {basic['total_routes']:,}")
    print(f"Unique route identifiers: {basic['unique_route_identifiers']:,}")
    print(f"Unique route numbers: {basic['unique_route_numbers']:,}")
    print(f"Total route pages: {basic['total_route_pages']:,}")
    
    # File info
    file_stats = results['file_stats']
    print(f"\nDataset Information:")
    print(f"  • Total lines: {file_stats['total_lines']:,}")
    print(f"  • File size: {file_stats['file_size_mb']:.2f} MB")
    
    # Page Analysis
    page = results['page_analysis']
    print("\n📄 ROUTE PAGES ANALYSIS")
    print("-" * 50)
    print(f"Single-paged routes: {page['single_paged_routes']:,} ({page['single_paged_routes']/basic['total_routes']*100:.1f}%)")
    print(f"Double-paged routes: {page['double_paged_routes']:,} ({page['double_paged_routes']/basic['total_routes']*100:.1f}%)")
    print(f"Triple-paged routes: {page['triple_paged_routes']:,} ({page['triple_paged_routes']/basic['total_routes']*100:.1f}%)")
    print(f"More than triple-paged: {page['more_than_triple_paged_routes']:,} ({page['more_than_triple_paged_routes']/basic['total_routes']*100:.1f}%)")
    print(f"\nMaximum pages for a route: {page['max_pages']}")
    print(f"Average pages per route: {page['avg_pages']:.2f}")
    
    # Stop Analysis
    stops = results['stop_analysis']
    print("\n🛑 STOPS ANALYSIS")
    print("-" * 50)
    print(f"Total stops across all routes: {stops['total_stops']:,}")
    print(f"Average stops per route: {stops['avg_stops_per_route']:.1f}")
    print(f"Minimum stops in a route: {stops['min_stops']}")
    print(f"Maximum stops in a route: {stops['max_stops']}")
    print(f"Median stops per route: {stops['median_stops']}")
    
    # Route Categories
    categories = results['route_categories']
    print("\n🚌 MAIN ROUTE CATEGORIES (TOP 15)")
    print("-" * 50)
    main_routes = categories['main_route_counts']
    for i, (route_num, count) in enumerate(list(main_routes.items())[:15], 1):
        percentage = (count / basic['total_routes']) * 100
        print(f"{i:2d}. Route {route_num}: {count:,} variations ({percentage:.1f}%)")
    
    if len(main_routes) > 15:
        remaining = sum(list(main_routes.values())[15:])
        print(f"    ... and {len(main_routes) - 15} more categories with {remaining:,} variations")
    print(f"\nTotal main route categories: {categories['total_categories']}")
    
    # Complexity Analysis
    complexity = results['complexity_analysis']
    print("\n🔧 ROUTE COMPLEXITY ANALYSIS")
    print("-" * 50)
    print(f"Simple routes (basic numbering): {complexity['simple_routes']:,}")
    print(f"Complex routes (sub-routes/variants): {complexity['complex_routes']:,}")
    
    print(f"\nMost complex routes:")
    for route, comp_score in complexity['most_complex_routes'][:5]:
        print(f"  • {route} (complexity: {comp_score})")
    
    # Geographic Analysis
    geo = results['geographic_analysis']
    print("\n🌍 GEOGRAPHIC ANALYSIS")
    print("-" * 50)
    print(f"Total unique cities/destinations: {geo['total_unique_cities']}")
    print(f"\nMost frequent destinations (TOP 10):")
    for i, (city, count) in enumerate(list(geo['top_cities'].items())[:10], 1):
        print(f"{i:2d}. {city}: {count} routes")
    
    # Sample Routes
    print("\n📋 SAMPLE ROUTES (First 15)")
    print("-" * 50)
    detailed = results['detailed_data']
    for i, (route_num, description, pages_data) in enumerate(detailed['sample_routes'][:15], 1):
        page_count = detailed['routes_by_page_count'].get(route_num, 0)
        stops_count = len(pages_data)
        print(f"{i:2d}. {route_num}: {description}")
        print(f"    └─ {page_count} page(s), {stops_count} stops")

def save_results_to_json(results: Dict, output_file: str):
    """Save detailed results to JSON file for further analysis."""
    # Remove sample data to make JSON cleaner
    clean_results = results.copy()
    clean_results['detailed_data']['sample_routes'] = []  # Remove heavy data
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(clean_results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Detailed results saved to: {output_file}")

def main():
    """Main function for enhanced analysis."""
    dataset_file = "into-csv/all-converted-content-fixed-cleared.txt"
    
    if not os.path.exists(dataset_file):
        print(f"❌ Error: Dataset file '{dataset_file}' not found!")
        return
    
    print("🚌 Enhanced Bus Routes Dataset Analysis")
    print("=" * 60)
    
    try:
        # Perform enhanced analysis
        results = analyze_bus_routes_enhanced(dataset_file)
        
        # Print comprehensive report
        print_enhanced_report(results)
        
        # Save detailed results
        save_results_to_json(results, "bus_routes_analysis_results.json")
        
        print("\n" + "=" * 90)
        print("✅ Enhanced analysis completed successfully!")
        print("=" * 90)
        
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()