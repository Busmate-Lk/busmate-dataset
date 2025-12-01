#!/usr/bin/env python3
"""
Final fix script to ensure perfect data integrity
Removes extra entries and ensures 1:1 mapping with original file
"""

import pandas as pd
from pathlib import Path

def final_fix():
    """
    Remove extra entries that don't exist in original file
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
    
    # Get valid IDs from original file
    valid_ids = set(original_df['stop_id'].tolist())
    
    # Filter final_df to only include valid IDs
    print(f"\nFiltering to only valid stop_ids...")
    invalid_entries = final_df[~final_df['stop_id'].isin(valid_ids)]
    
    if not invalid_entries.empty:
        print(f"Removing {len(invalid_entries)} invalid entries:")
        for _, row in invalid_entries.iterrows():
            print(f"  - Removing invalid stop_id {row['stop_id']}: {row['stop_name_sinhala']}")
    
    # Keep only valid entries
    final_df = final_df[final_df['stop_id'].isin(valid_ids)].reset_index(drop=True)
    
    # Sort by stop_id
    final_df = final_df.sort_values('stop_id').reset_index(drop=True)
    
    print(f"\nFinal stops after fix: {len(final_df)}")
    print(f"Original stops: {len(original_df)}")
    
    # Final verification
    if len(final_df) == len(original_df):
        print("✅ Perfect data integrity achieved!")
        
        # Check for any remaining missing IDs
        final_ids = set(final_df['stop_id'].tolist())
        missing_ids = valid_ids - final_ids
        if missing_ids:
            print(f"⚠️  Still missing {len(missing_ids)} IDs: {sorted(list(missing_ids))}")
        else:
            print("✅ All original stop_ids are present")
            
    else:
        print("❌ Count still doesn't match")
    
    # Save final corrected file
    final_df.to_csv(final_file, index=False, encoding='utf-8')
    print(f"✅ Final file updated: {final_file}")
    
    # Add English translations for the missing entries
    missing_english = final_df[final_df['stop_name_english'] == '']
    if not missing_english.empty:
        print(f"\nAdding English translations for {len(missing_english)} entries...")
        
        # Add translations for the known missing entries
        translations = {
            2034: "Telbaduar (Sri Pushparamaya)",
            4327: "Sisiravatta Handiya Bodhiya"
        }
        
        for idx, row in missing_english.iterrows():
            stop_id = row['stop_id']
            if stop_id in translations:
                final_df.at[idx, 'stop_name_english'] = translations[stop_id]
                print(f"  - Added translation for {stop_id}: {translations[stop_id]}")
        
        # Save again with translations
        final_df.to_csv(final_file, index=False, encoding='utf-8')
        print("✅ Added English translations")
    
    print(f"\n🎉 FINAL DATASET READY!")
    print(f"📍 Location: {final_file}")
    print(f"📊 Total stops: {len(final_df):,}")
    print(f"📍 Stops with location data: {final_df['city'].notna().sum():,}")
    print(f"🌍 Coverage: {final_df['city'].notna().sum()/len(final_df)*100:.1f}% have location data")

if __name__ == "__main__":
    final_fix()