#!/usr/bin/env python3
"""
Simple script to correct bus stop names in unique_stops.csv using corrections
from mistaken_stops_list.csv and output to unique_stops_corrected.csv
"""

import pandas as pd
from pathlib import Path

def correct_stop_names_simple():
    """
    Simple function to correct stop names without interactive prompts
    """
    # Define file paths (assumes script is in the same directory as the CSV files)
    current_dir = Path(__file__).parent
    unique_stops_file = current_dir / "unique_stops.csv"
    mistaken_stops_file = current_dir / "mistaken_stops_list.csv"
    output_file = current_dir / "unique_stops_corrected.csv"
    
    try:
        # Read the CSV files
        print("Reading CSV files...")
        unique_stops_df = pd.read_csv(unique_stops_file)
        mistaken_stops_df = pd.read_csv(mistaken_stops_file)
        
        # Create a mapping dictionary from mistaken names to corrected names
        corrections_map = dict(zip(
            mistaken_stops_df['mistaken_stop_name'], 
            mistaken_stops_df['corrected_stop_name']
        ))
        
        # Make a copy and apply corrections
        corrected_df = unique_stops_df.copy()
        corrections_applied = 0
        
        # Apply corrections by replacing stop names
        for index, row in corrected_df.iterrows():
            stop_name = row['stop_name']
            if stop_name in corrections_map:
                corrected_df.at[index, 'stop_name'] = corrections_map[stop_name]
                corrections_applied += 1
        
        # Save the corrected data
        corrected_df.to_csv(output_file, index=False, encoding='utf-8')
        
        # Print summary
        print(f"✓ Corrections applied: {corrections_applied}")
        print(f"✓ Total stops: {len(corrected_df)}")
        print(f"✓ Output saved: {output_file}")
        
        return corrected_df, corrections_applied
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None, 0

if __name__ == "__main__":
    print("Bus Stop Name Correction Tool (Simple Version)")
    print("=" * 50)
    corrected_df, corrections_count = correct_stop_names_simple()
    
    if corrected_df is not None:
        print(f"\n✓ Successfully corrected {corrections_count} stop names!")
    else:
        print("\n✗ Failed to process the files.")