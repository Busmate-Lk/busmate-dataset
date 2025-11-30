#!/usr/bin/env python3
"""
Script to convert imported stops JSON log to CSV format
Extracts importedStops from JSON and creates a CSV file for data pipeline usage
"""

import json
import csv
import sys
from pathlib import Path

def convert_json_to_csv(json_file_path, csv_file_path=None):
    """
    Convert imported stops JSON log to CSV format
    
    Args:
        json_file_path (str): Path to the JSON import log file
        csv_file_path (str): Path for output CSV file (optional)
    
    Returns:
        str: Path to the created CSV file
    """
    
    # Default CSV file path if not provided
    if csv_file_path is None:
        json_path = Path(json_file_path)
        csv_file_path = json_path.parent / f"{json_path.stem}.csv"
    
    try:
        # Read JSON file
        print(f"Reading JSON file: {json_file_path}")
        with open(json_file_path, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)
        
        # Extract imported stops
        imported_stops = data.get('importedStops', [])
        
        if not imported_stops:
            print("No imported stops found in the JSON file!")
            return None
        
        print(f"Found {len(imported_stops)} imported stops")
        
        # CSV headers
        headers = ['uuid', 'stop_name', 'original_stop_id', 'row_number']
        
        # Write to CSV
        print(f"Writing CSV file: {csv_file_path}")
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            
            # Write header
            writer.writerow(headers)
            
            # Write data
            for stop in imported_stops:
                writer.writerow([
                    stop.get('id', ''),
                    stop.get('name', ''),
                    stop.get('originalStopId', ''),
                    stop.get('rowNumber', '')
                ])
        
        print(f"✅ Successfully converted {len(imported_stops)} stops to CSV")
        print(f"📁 CSV file created: {csv_file_path}")
        
        # Print summary statistics
        print("\n📊 Import Summary:")
        print(f"   Total Records: {data.get('totalRecords', 'N/A')}")
        print(f"   Successful Imports: {data.get('successfulImports', 'N/A')}")
        print(f"   Failed Imports: {data.get('failedImports', 'N/A')}")
        print(f"   Message: {data.get('message', 'N/A')}")
        
        return str(csv_file_path)
        
    except FileNotFoundError:
        print(f"❌ Error: JSON file not found: {json_file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def main():
    """Main function to handle command line arguments"""
    
    if len(sys.argv) < 2:
        print("Usage: python convert_import_log.py <json_file_path> [csv_file_path]")
        print("Example: python convert_import_log.py import_2025-11-30_1.json")
        print("Example: python convert_import_log.py import_2025-11-30_1.json stops_mapping.csv")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    csv_file_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Convert JSON to CSV
    result = convert_json_to_csv(json_file_path, csv_file_path)
    
    if result:
        print(f"\n🎉 Conversion completed successfully!")
        print(f"📋 You can now use '{result}' in your data pipeline")
        print(f"💡 The CSV contains UUID mappings for importing routes and schedules")
    else:
        print("\n❌ Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()