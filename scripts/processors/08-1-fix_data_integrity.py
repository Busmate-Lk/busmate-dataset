#!/usr/bin/env python3
"""
Quick fix script to resolve data integrity issues in final_unique_stops.csv
Fixes duplicate stop_ids and adds missing entries
"""

import pandas as pd
from pathlib import Path

def fix_data_integrity():
    """
    Fix the duplicate and missing stop_id issues
    """
    # Define paths
    base_path = Path(__file__).parent.parent.parent
    original_file = base_path / "staging/step-6-normalized_data/unique_stops.csv"
    final_file = base_path / "staging/step-8-anomaly_correcting/final_unique_stops.csv"
    
    print("Reading files...")
    original_df = pd.read_csv(original_file)
    final_df = pd.read_csv(final_file)
    
    print(f"Original stops: {len(original_df)}")
    print(f"Final stops before fix: {len(final_df)}")
    
    # Fix duplicate stop_ids by removing duplicates (keep first occurrence)
    print("\nFixing duplicates...")
    duplicates = final_df[final_df['stop_id'].duplicated(keep='first')]
    print(f"Removing {len(duplicates)} duplicate entries:")
    for _, row in duplicates.iterrows():
        print(f"  - Removing duplicate stop_id {row['stop_id']}: {row['stop_name_sinhala']}")
    
    final_df = final_df.drop_duplicates(subset=['stop_id'], keep='first').reset_index(drop=True)
    
    # Add missing stop_ids from original file
    print("\nAdding missing entries...")
    final_ids = set(final_df['stop_id'].tolist())
    original_ids = set(original_df['stop_id'].tolist())
    missing_ids = original_ids - final_ids
    
    for missing_id in sorted(missing_ids):
        original_row = original_df[original_df['stop_id'] == missing_id].iloc[0]
        print(f"  - Adding missing stop_id {missing_id}: {original_row['stop_name']}")
        
        # Create new row with missing data
        new_row = {
            'stop_id': missing_id,
            'stop_name_sinhala': original_row['stop_name'],
            'stop_name_english': '',  # Empty, needs manual correction
            'city': '',
            'state': ''
        }
        final_df = pd.concat([final_df, pd.DataFrame([new_row])], ignore_index=True)
    
    # Sort by stop_id
    final_df = final_df.sort_values('stop_id').reset_index(drop=True)
    
    print(f"\nFinal stops after fix: {len(final_df)}")
    print(f"Should match original: {len(original_df)}")
    
    # Verify fix
    if len(final_df) == len(original_df):
        print("✅ Data integrity fixed!")
    else:
        print("❌ Still have count mismatch")
    
    # Save corrected file
    final_df.to_csv(final_file, index=False, encoding='utf-8')
    print(f"✅ Updated: {final_file}")
    
    # Show entries that need manual English translation
    missing_english = final_df[final_df['stop_name_english'] == '']
    if not missing_english.empty:
        print(f"\n⚠️  {len(missing_english)} entries need English translation:")
        for _, row in missing_english.iterrows():
            print(f"  - {row['stop_id']}: {row['stop_name_sinhala']}")

if __name__ == "__main__":
    fix_data_integrity()