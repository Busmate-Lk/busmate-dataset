#!/usr/bin/env python3
"""
Script to create final_unique_routes.csv by merging original routes with corrected routes.
This combines the original unique_routes.csv with the anomaly-corrected routes.
"""

import pandas as pd
import os
from pathlib import Path

def create_final_routes():
    """
    Create final_unique_routes.csv by replacing corrected routes in original data.
    """
    # Define file paths using absolute paths
    base_dir = Path("/home/kavinda/Desktop/Desktop/BusMate/dataset")
    original_file = base_dir / "staging" / "step-6-normalized_data" / "unique_routes.csv"
    corrected_file = base_dir / "staging" / "step-8-anomaly_correcting" / "corrected_routes.csv"
    output_file = base_dir / "staging" / "step-8-anomaly_correcting" / "final_unique_routes.csv"
    
    # Check if input files exist
    if not original_file.exists():
        raise FileNotFoundError(f"Original file not found: {original_file}")
    
    if not corrected_file.exists():
        raise FileNotFoundError(f"Corrected file not found: {corrected_file}")
    
    print(f"Reading original routes from: {original_file}")
    print(f"Reading corrected routes from: {corrected_file}")
    
    # Read the original routes
    original_df = pd.read_csv(original_file)
    print(f"Original routes count: {len(original_df)}")
    
    # Read the corrected routes
    corrected_df = pd.read_csv(corrected_file)
    print(f"Corrected routes count: {len(corrected_df)}")
    
    # Create final dataset by replacing corrected routes
    # Get the route_ids that were corrected
    corrected_route_ids = set(corrected_df['route_id'])
    print(f"Route IDs that were corrected: {len(corrected_route_ids)}")
    
    # Split original data into corrected and non-corrected routes
    non_corrected_df = original_df[~original_df['route_id'].isin(corrected_route_ids)].copy()
    
    # Combine non-corrected routes with corrected routes
    final_df = pd.concat([non_corrected_df, corrected_df], ignore_index=True)
    
    replaced_count = len(corrected_route_ids)
    unchanged_count = len(non_corrected_df)
    
    print(f"Successfully merged {replaced_count} corrected routes with {unchanged_count} unchanged routes")
    
    # Verify the final count matches original
    if len(final_df) != len(original_df):
        raise ValueError(f"Final route count ({len(final_df)}) doesn't match original ({len(original_df)})")
    
    # Sort by route_id for consistency
    final_df = final_df.sort_values('route_id').reset_index(drop=True)
    
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save the final merged routes
    final_df.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Final routes saved to: {output_file}")
    print(f"Final routes count: {len(final_df)}")
    
    # Generate summary report
    print("\n" + "="*50)
    print("FINAL ROUTES CREATION SUMMARY")
    print("="*50)
    print(f"Original routes: {len(original_df)}")
    print(f"Corrected routes: {len(corrected_df)}")
    print(f"Unchanged routes: {unchanged_count}")
    print(f"Final total routes: {len(final_df)}")
    print(f"Output file: {output_file}")
    print("="*50)
    
    return output_file

if __name__ == "__main__":
    try:
        output_file = create_final_routes()
        print(f"\n✅ Successfully created final routes file: {output_file}")
    except Exception as e:
        print(f"\n❌ Error creating final routes: {str(e)}")
        exit(1)