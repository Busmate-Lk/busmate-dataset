# Data Dictionary

### Routes Data Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `route_id` | string | Yes | Unique identifier (format: R###) |
| `route_number` | string | Yes | Display route number (e.g., "100", "138/1") |
| `route_name` | string | Yes | Descriptive route name |
| `operator` | string | Yes | Bus operator (SLTB/Private/CTB) |
| `route_type` | string | No | Route classification |
| `direction` | string | No | Route direction (UP/DOWN/CIRCULAR) |
| `stops` | array | Yes | Array of stop objects |
| `fare_stages` | array | No | Fare stage information |
| `total_stops` | integer | No | Calculated total stops |
| `route_distance_km` | number | No | Calculated route distance |
| `status` | string | No | Route operational status |
| `metadata` | object | No | Processing metadata |

### Stops Data Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stop_id` | string | Yes | Unique stop identifier |
| `stop_name` | string | Yes | Primary stop name |
| `stop_name_sinhala` | string | No | Sinhala translation |
| `stop_name_tamil` | string | No | Tamil translation |
| `sequence` | integer | No | Stop order in route |
| `latitude` | number | No | GPS latitude |
| `longitude` | number | No | GPS longitude |
| `district` | string | No | Administrative district |
| `province` | string | No | Administrative province |
| `stop_type` | string | No | Stop classification |
| `facilities` | array | No | Available facilities |

### Fare Stages Data Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stage_id` | string | Yes | Unique stage identifier |
| `from_stop_name` | string | Yes | Starting stop |
| `to_stop_name` | string | Yes | Ending stop |
| `distance_km` | number | No | Stage distance |
| `fare_normal` | number | Yes | Regular bus fare |
| `fare_semi_luxury` | number | No | Semi-luxury fare |
| `fare_luxury` | number | No | Luxury bus fare |
| `fare_intercity` | number | No | Intercity fare |
| `effective_from` | string | No | Fare effective date |
