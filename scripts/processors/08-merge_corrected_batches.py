#!/usr/bin/env python3
"""
Script to merge corrected batch files into final_unique_stops.csv
Combines original unique_stops.csv with all corrected batch files from step-8
"""

import pandas as pd
import os
import glob
from pathlib import Path

def merge_corrected_batches():
    """
    Merge all corrected batch files into a single final_unique_stops.csv
    """
    # Define paths
    base_path = Path(__file__).parent.parent.parent
    original_file = base_path / "staging/step-6-normalized_data/unique_stops.csv"
    corrected_dir = base_path / "staging/step-8-anomaly_correcting/corrected-stops"
    output_file = base_path / "staging/step-8-anomaly_correcting/final_unique_stops.csv"
    
    print(f"Reading original file: {original_file}")
    print(f"Reading corrected batches from: {corrected_dir}")
    print(f"Output file: {output_file}")
    
    # Read original file to get total count and verify structure
    original_df = pd.read_csv(original_file)
    print(f"Original file has {len(original_df)} stops")
    
    # Find all corrected batch files
    batch_files = sorted(glob.glob(str(corrected_dir / "corrected_stops_batch_*.csv")))
    print(f"Found {len(batch_files)} batch files")
    
    if not batch_files:
        raise FileNotFoundError(f"No corrected batch files found in {corrected_dir}")
    
    # Read and combine all batch files
    corrected_dfs = []
    total_corrected_stops = 0
    
    for batch_file in batch_files:
        batch_num = batch_file.split('_batch_')[1].split('.')[0]
        print(f"Processing batch {batch_num}...")
        
        df = pd.read_csv(batch_file)
        corrected_dfs.append(df)
        total_corrected_stops += len(df)
        print(f"  - Batch {batch_num}: {len(df)} stops")
    
    # Combine all corrected batches
    print(f"\nCombining {len(corrected_dfs)} batch files...")
    final_df = pd.concat(corrected_dfs, ignore_index=True)
    
    # Sort by stop_id to ensure proper order
    final_df = final_df.sort_values('stop_id').reset_index(drop=True)
    
    # Verify data integrity
    print(f"\nData integrity check:")
    print(f"Original stops: {len(original_df)}")
    print(f"Corrected stops: {len(final_df)}")
    print(f"Missing stops: {len(original_df) - len(final_df)}")
    
    # Check for duplicate stop_ids
    duplicates = final_df[final_df['stop_id'].duplicated()]
    if not duplicates.empty:
        print(f"WARNING: Found {len(duplicates)} duplicate stop_ids:")
        print(duplicates[['stop_id', 'stop_name_sinhala']].head())
    
    # Check for missing stop_ids
    original_ids = set(original_df['stop_id'].tolist())
    corrected_ids = set(final_df['stop_id'].tolist())
    missing_ids = original_ids - corrected_ids
    
    if missing_ids:
        print(f"WARNING: Missing {len(missing_ids)} stop_ids in corrected data:")
        print(f"Missing IDs: {sorted(list(missing_ids))[:10]}..." if len(missing_ids) > 10 else f"Missing IDs: {sorted(list(missing_ids))}")
    
    # Display sample of final data
    print(f"\nFinal dataset summary:")
    print(f"Columns: {list(final_df.columns)}")
    print(f"Total rows: {len(final_df)}")
    print(f"Rows with city data: {final_df['city'].notna().sum()}")
    print(f"Rows with state data: {final_df['state'].notna().sum()}")
    
    print(f"\nSample of final data:")
    print(final_df.head())
    
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save final merged file
    final_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"\n✅ Successfully created: {output_file}")
    print(f"Final file contains {len(final_df)} stops with enhanced data")
    
    # Generate summary report
    print(f"\n📊 FINAL SUMMARY REPORT:")
    print(f"=" * 50)
    print(f"Total bus stops processed: {len(final_df):,}")
    print(f"Stops with location data: {final_df['city'].notna().sum():,}")
    print(f"Unique cities: {final_df['city'].nunique()}")
    print(f"Unique states: {final_df['state'].nunique()}")
    print(f"Coverage: {final_df['city'].notna().sum()/len(final_df)*100:.1f}% have location data")
    
    # Show distribution by state
    if final_df['state'].notna().any():
        print(f"\nStops by state:")
        state_counts = final_df['state'].value_counts()
        for state, count in state_counts.items():
            print(f"  {state}: {count} stops")
    
    return output_file

if __name__ == "__main__":
    try:
        output_path = merge_corrected_batches()
        print(f"\n🎉 Process completed successfully!")
        print(f"Final output: {output_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
        raise