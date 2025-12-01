#!/usr/bin/env python3
"""
Script to create final_bus_routes.csv by combining route and stop data
Merges bus_routes.csv with cleaned final_unique_routes.csv and final_unique_stops.csv
"""

import pandas as pd
import os
from pathlib import Path
from difflib import get_close_matches
import re

def normalize_stop_name(stop_name):
    """
    Normalize stop name for better matching
    """
    if pd.isna(stop_name):
        return ""
    
    # Convert to string and strip whitespace
    name = str(stop_name).strip()
    
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name)
    
    return name

def find_best_match(stop_name, stop_lookup, threshold=0.6):
    """
    Find the best matching stop from the cleaned stops dataset
    """
    if not stop_name:
        return None
    
    # Direct match first
    if stop_name in stop_lookup:
        return stop_lookup[stop_name]
    
    # Try fuzzy matching
    matches = get_close_matches(stop_name, stop_lookup.keys(), n=1, cutoff=threshold)
    if matches:
        return stop_lookup[matches[0]]
    
    return None

def create_final_bus_routes():
    """
    Create final_bus_routes.csv with enhanced route and stop information
    """
    # Define paths
    base_path = Path(__file__).parent.parent.parent
    original_routes_file = base_path / "staging/step-5-basic_csv/bus_routes.csv"
    final_routes_file = base_path / "staging/step-8-anomaly_correcting/final_unique_routes.csv"
    final_stops_file = base_path / "staging/step-8-anomaly_correcting/final_unique_stops.csv"
    output_file = base_path / "staging/step-9-final_processed/final_bus_routes.csv"
    
    print(f"Reading input files...")
    print(f"Original routes: {original_routes_file}")
    print(f"Final routes: {final_routes_file}")
    print(f"Final stops: {final_stops_file}")
    print(f"Output: {output_file}")
    
    # Read input files
    print(f"\nLoading datasets...")
    original_routes_df = pd.read_csv(original_routes_file)
    final_routes_df = pd.read_csv(final_routes_file)
    final_stops_df = pd.read_csv(final_stops_file)
    
    print(f"Original routes data: {len(original_routes_df):,} entries")
    print(f"Final routes: {len(final_routes_df):,} routes")
    print(f"Final stops: {len(final_stops_df):,} stops")
    
    # Create lookup dictionaries
    print(f"\nCreating lookup dictionaries...")
    
    # Route lookup: route_number -> route metadata
    route_lookup = {}
    for _, row in final_routes_df.iterrows():
        route_lookup[row['route_number']] = {
            'route_id': row['route_id'],
            'route_name_cleaned': row['route_name'],
            'route_through_cleaned': row['route_through'],
            'total_stops': row['stops_count']
        }
    
    # Stop lookup: original_stop_name -> enhanced stop data
    stop_lookup = {}
    for _, row in final_stops_df.iterrows():
        # Use original stop name from step-6 data as key for matching
        stop_lookup[row['stop_name_sinhala']] = {
            'stop_id': row['stop_id'],
            'stop_name_sinhala': row['stop_name_sinhala'],
            'stop_name_english': row['stop_name_english'],
            'city': row['city'] if pd.notna(row['city']) else '',
            'state': row['state'] if pd.notna(row['state']) else ''
        }
    
    print(f"Route lookup: {len(route_lookup):,} routes")
    print(f"Stop lookup: {len(stop_lookup):,} stops")
    
    # Process original routes data
    print(f"\nProcessing route-stop relationships...")
    
    processed_routes = []
    matched_stops = 0
    unmatched_stops = []
    processed_count = 0
    
    for idx, row in original_routes_df.iterrows():
        if idx % 5000 == 0:
            print(f"  Processing row {idx:,}/{len(original_routes_df):,} ({idx/len(original_routes_df)*100:.1f}%)")
        
        route_number = row['route_number']
        stop_name = normalize_stop_name(row['stop_name'])
        
        # Get route metadata
        route_meta = route_lookup.get(route_number, {})
        
        # Find matching stop
        stop_match = find_best_match(stop_name, stop_lookup)
        
        if stop_match:
            matched_stops += 1
            stop_id = stop_match['stop_id']
            stop_name_english = stop_match['stop_name_english']
            city = stop_match['city']
            state = stop_match['state']
        else:
            unmatched_stops.append(stop_name)
            stop_id = None
            stop_name_english = ''
            city = ''
            state = ''
        
        # Create processed route entry
        processed_entry = {
            'route_id': route_meta.get('route_id', ''),
            'route_number': route_number,
            'route_name': route_meta.get('route_name_cleaned', row['route_name']),
            'route_through': route_meta.get('route_through_cleaned', row['route_through']),
            'total_stops': route_meta.get('total_stops', ''),
            'stop_sequence': row['stop_sequence'],
            'stop_id': stop_id,
            'stop_name_sinhala': stop_name,
            'stop_name_english': stop_name_english,
            'city': city,
            'state': state,
            'fare_from_start': row['fare_from_start']
        }
        
        processed_routes.append(processed_entry)
        processed_count += 1
    
    # Create final DataFrame
    print(f"\nCreating final dataset...")
    final_df = pd.DataFrame(processed_routes)
    
    # Sort by route_number and stop_sequence
    final_df = final_df.sort_values(['route_number', 'stop_sequence']).reset_index(drop=True)
    
    # Create output directory
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save final file
    final_df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n✅ Successfully created: {output_file}")
    print(f"📊 PROCESSING SUMMARY:")
    print(f"=" * 50)
    print(f"Total route entries processed: {processed_count:,}")
    print(f"Matched stops: {matched_stops:,} ({matched_stops/processed_count*100:.1f}%)")
    print(f"Unmatched stops: {len(unmatched_stops):,} ({len(unmatched_stops)/processed_count*100:.1f}%)")
    print(f"Unique routes: {final_df['route_number'].nunique():,}")
    print(f"Unique stops: {final_df['stop_name_sinhala'].nunique():,}")
    
    # Show sample of final data
    print(f"\nSample of final data:")
    print(final_df.head(10).to_string(index=False))
    
    # Show some unmatched stops for review
    if unmatched_stops:
        unique_unmatched = list(set(unmatched_stops))[:10]
        print(f"\nSample unmatched stops (first 10):")
        for stop in unique_unmatched:
            print(f"  - {stop}")
    
    # Show stats by route
    route_stats = final_df.groupby('route_number').agg({
        'stop_sequence': 'count',
        'stop_id': lambda x: x.notna().sum(),
        'city': lambda x: (x != '').sum(),
        'state': lambda x: (x != '').sum()
    }).round(2)
    
    route_stats.columns = ['total_stops', 'matched_stops', 'stops_with_city', 'stops_with_state']
    route_stats['match_rate'] = (route_stats['matched_stops'] / route_stats['total_stops'] * 100).round(1)
    
    print(f"\nTop 10 routes by stop count:")
    top_routes = route_stats.sort_values('total_stops', ascending=False).head(10)
    print(top_routes.to_string())
    
    return output_file

if __name__ == "__main__":
    try:
        output_path = create_final_bus_routes()
        print(f"\n🎉 Step 9 completed successfully!")
        print(f"Final output: {output_path}")
        print(f"\nYour comprehensive bus routes dataset is ready for the BusMate system! 🚌")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise