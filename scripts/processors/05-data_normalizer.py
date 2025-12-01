#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import sys
import argparse
import unicodedata
from pathlib import Path


def normalize_sinhala(text: str) -> str:
    """
    Normalize Sinhala (and Tamil) text to NFC form.
    This fixes the "මෝදර" vs "මෝදර" issue permanently.
    """
    if not text:
        return ""
    # First strip whitespace, then normalize to NFC (composed form)
    return unicodedata.normalize("NFC", text.strip())


def normalize_data(input_file, unique_stops_file, unique_routes_file):
    """
    Split bus_routes.csv into two normalized files:
    - unique_stops.csv: All unique bus stops with IDs (Sinhala-normalized)
    - unique_routes.csv: All unique routes with IDs and stop counts
    """

    # Read the original CSV data
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            data = list(reader)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found.")
        return None, None
    except Exception as e:
        print(f"Error reading input file: {e}")
        return None, None

    print(f"Loaded {len(data):,} route entries from '{input_file}'")

    # ========================
    # Extract UNIQUE STOPS (with Sinhala normalization)
    # ========================
    unique_stops_set = set()

    for row in data:
        raw_name = row.get('stop_name', '') or ''
        normalized_name = normalize_sinhala(raw_name)
        if normalized_name:
            unique_stops_set.add(normalized_name)

    # Create final list with sequential IDs
    unique_stops = []
    for stop_id, stop_name in enumerate(sorted(unique_stops_set), 1):
        unique_stops.append({
            'stop_id': stop_id,
            'stop_name': stop_name
        })

    # ========================
    # Extract UNIQUE ROUTES
    # ========================
    unique_routes_set = set()
    route_stop_counts = {}

    for row in data:
        route_key = (
            row['route_number'].strip(),
            row['route_name'].strip(),
            row['route_through'].strip() if row['route_through'] else ''
        )

        if route_key not in unique_routes_set:
            unique_routes_set.add(route_key)
            route_stop_counts[route_key] = 1
        else:
            route_stop_counts[route_key] += 1

    unique_routes = []
    for route_id, route_key in enumerate(sorted(unique_routes_set), 1):
        route_number, route_name, route_through = route_key
        stops_count = route_stop_counts[route_key]

        unique_routes.append({
            'route_id': route_id,
            'route_number': route_number,
            'route_name': route_name,
            'route_through': route_through,
            'stops_count': stops_count
        })

    # ========================
    # Write unique_stops.csv
    # ========================
    try:
        with open(unique_stops_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['stop_id', 'stop_name']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_stops)
        print(f"Unique stops saved → {unique_stops_file}")
        print(f"   Total unique stops: {len(unique_stops):,}")
    except Exception as e:
        print(f"Error writing stops file: {e}")
        return None, None

    # ========================
    # Write unique_routes.csv
    # ========================
    try:
        with open(unique_routes_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['route_id', 'route_number', 'route_name', 'route_through', 'stops_count']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(unique_routes)
        print(f"Unique routes saved → {unique_routes_file}")
        print(f"   Total unique routes: {len(unique_routes):,}")
    except Exception as e:
        print(f"Error writing routes file: {e}")
        return None, None

    return unique_stops, unique_routes


def main():
    # Get the script's directory to build relative paths
    script_dir = Path(__file__).resolve().parent.parent.parent  # Adjust if needed

    # Default paths
    default_input = script_dir / "staging/step-5-basic_csv/bus_routes.csv"
    default_stops_output = script_dir / "staging/step-6-normalized_data/unique_stops.csv"
    default_routes_output = script_dir / "staging/step-6-normalized_data/unique_routes.csv"

    parser = argparse.ArgumentParser(
        description='Generate normalized unique_stops.csv and unique_routes.csv (with Sinhala Unicode fix)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Default paths (no args):
  Input:           {default_input}
  Stops Output:    {default_stops_output}
  Routes Output:   {default_routes_output}
        """
    )
    parser.add_argument('-i', '--input', help='Input bus_routes.csv path')
    parser.add_argument('-so', '--stops-output', help='Output unique_stops.csv path')
    parser.add_argument('-ro', '--routes-output', help='Output unique_routes.csv path')

    args = parser.parse_args()

    input_file = args.input or str(default_input)
    stops_output = args.stops_output or str(default_stops_output)
    routes_output = args.routes_output or str(default_routes_output)

    # Create output directories
    Path(stops_output).parent.mkdir(parents=True, exist_ok=True)
    Path(routes_output).parent.mkdir(parents=True, exist_ok=True)

    print("Sinhala Unicode normalization enabled (NFC)")
    print(f"Input:  {input_file}")
    print(f"Stops:  {stops_output}")
    print(f"Routes: {routes_output}")
    print("-" * 60)

    unique_stops, unique_routes = normalize_data(input_file, stops_output, routes_output)

    if unique_stops and unique_routes:
        print("\nSample unique stops:")
        print("stop_id,stop_name")
        for s in unique_stops[:10]:
            print(f"{s['stop_id']},{s['stop_name']}")
        if len(unique_stops) > 10:
            print(f"... and {len(unique_stops) - 10:,} more")

        print(f"\nProcessing complete!")


if __name__ == "__main__":
    main()