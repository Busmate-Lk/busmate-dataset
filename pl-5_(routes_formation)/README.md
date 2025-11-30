# Bus Route Stop Name Correction Process

## Overview
This directory contains the corrected bus route data with fixed stop names using the corrections identified in the stops filtration process.

## Files

### `correct_route_stops.py`
Main Python script that performs the stop name correction process.

**Input Files:**
- `../pl-3_(csv-formation)/bus_routes_structured.csv` - Original bus routes data
- `../pl-4_(stops-filtration)/mistaken_stops_list.csv` - Correction mappings
- `../pl-4_(stops-filtration)/unique_stops_corrected.csv` - Reference for validation

**Output:**
- `bus_routes_corrected.csv` - Corrected bus routes with fixed stop names

## Correction Results

### Statistics
- **Total route records processed:** 58,933
- **Total corrections applied:** 1,373 instances
- **Unique stop name corrections:** 127 different corrections
- **Unique routes:** 613
- **Unique stops after correction:** 4,479

### Process Description
1. **Load Corrections:** The script reads the mistaken → corrected stop name mappings from `mistaken_stops_list.csv`
2. **Apply Corrections:** Goes through each record in `bus_routes_structured.csv` and replaces any mistaken stop names with their corrected versions
3. **Validation:** Cross-references all corrected stop names against the validated unique stops list to ensure accuracy
4. **Output:** Saves the corrected data to `bus_routes_corrected.csv`

### Key Corrections Applied
The script corrected duplicate/redundant stop names such as:
- `උතුවන්කන්ද උතුවන්කන්ද` → `උතුවන්කන්ද`
- `තන්නිමලේ තන්නිමලේ` → `තන්නිමලේ`
- `සේනකුඩි ඉරිප්පු සේනකුඩි ඉරිප්පු` → `සේනකුඩි ඉරිප්පු`

And many others where the stop name was erroneously duplicated.

## Data Quality
✅ **All corrected stop names validated** against the unique stops reference
✅ **No data loss** - all original route information preserved
✅ **Consistent formatting** maintained throughout

## Usage
To run the correction process:
```bash
cd pl-5_(routes_formation)
python correct_route_stops.py
```

The script will automatically:
1. Locate and read all required input files
2. Apply corrections systematically
3. Validate the results
4. Generate detailed output with correction statistics
5. Save the corrected data

## Next Steps
The corrected `bus_routes_corrected.csv` file is now ready for:
- Database import
- API integration
- Application development
- Further data processing or analysis