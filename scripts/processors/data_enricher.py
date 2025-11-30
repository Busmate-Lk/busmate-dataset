#!/usr/bin/env python3
"""
Data Enricher Module
Enriches processed data with additional information and validations.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import csv

logger = logging.getLogger(__name__)

class DataEnricher:
    """Enriches processed route and stop data."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize data enricher.
        
        Args:
            config: Configuration dictionary with enrichment settings
        """
        self.config = config or {}
        self.geocoding_enabled = self.config.get('geocoding_enabled', False)
        self.fare_calculation = self.config.get('fare_calculation', True)
        
    def enrich_routes(self, routes: List[Dict], output_path: Optional[str] = None) -> List[Dict]:
        """
        Enrich route data with additional information.
        
        Args:
            routes: List of route dictionaries
            output_path: Optional path to save enriched data
            
        Returns:
            List of enriched route dictionaries
        """
        logger.info(f"Enriching {len(routes)} routes")
        
        enriched_routes = []
        
        for route in routes:
            enriched_route = self._enrich_single_route(route)
            enriched_routes.append(enriched_route)
            
        if output_path:
            self._save_enriched_data(enriched_routes, output_path)
            
        logger.info("Route enrichment completed")
        return enriched_routes
        
    def _enrich_single_route(self, route: Dict) -> Dict:
        """Enrich a single route with additional data."""
        enriched = route.copy()
        
        # Add metadata
        enriched['metadata'] = {
            'processed_at': self._get_current_timestamp(),
            'data_source': 'ntc_pdf',
            'confidence_score': self._calculate_confidence_score(route),
            'validation_status': 'pending'
        }
        
        # Add calculated fields
        if 'stops' in route and len(route['stops']) > 1:
            enriched['total_stops'] = len(route['stops'])
            enriched['route_distance_km'] = self._calculate_route_distance(route['stops'])
            
        # Add route classification
        enriched['route_type'] = self._classify_route(route)
        
        # Add fare information if enabled
        if self.fare_calculation and 'stops' in route:
            enriched['fare_stages'] = self._generate_fare_stages(route['stops'])
            
        return enriched
        
    def _calculate_confidence_score(self, route: Dict) -> float:
        """Calculate confidence score for route data quality."""
        score = 0.0
        max_score = 100.0
        
        # Route number present and valid
        if 'route_number' in route and route['route_number']:
            score += 20.0
            
        # Route name present
        if 'route_name' in route and route['route_name']:
            score += 15.0
            
        # Operator information present
        if 'operator' in route and route['operator']:
            score += 15.0
            
        # Minimum number of stops
        if 'stops' in route and len(route['stops']) >= 2:
            score += 25.0
            if len(route['stops']) >= 5:
                score += 10.0
                
        # Stop names quality
        if 'stops' in route:
            valid_stops = sum(1 for stop in route['stops'] 
                            if isinstance(stop, dict) and 
                            stop.get('stop_name', '').strip())
            if valid_stops > 0:
                score += (valid_stops / len(route['stops'])) * 15.0
                
        return min(score, max_score)
        
    def _classify_route(self, route: Dict) -> str:
        """Classify route type based on characteristics."""
        route_number = route.get('route_number', '').upper()
        route_name = route.get('route_name', '').lower()
        
        # Express routes
        if 'express' in route_name or route_number.startswith('E'):
            return 'EXPRESS'
            
        # Intercity routes
        if any(keyword in route_name for keyword in ['intercity', 'ic', 'highway']):
            return 'INTERCITY'
            
        # School routes
        if 'school' in route_name or route_number.startswith('S'):
            return 'SCHOOL'
            
        # Circular routes
        if 'circular' in route_name or 'circle' in route_name:
            return 'CIRCULAR'
            
        # Default to regular
        return 'REGULAR'
        
    def _calculate_route_distance(self, stops: List[Dict]) -> float:
        """Calculate approximate route distance."""
        # Placeholder implementation - would need actual coordinates
        # For now, estimate based on number of stops
        return len(stops) * 1.5  # Assume 1.5km average between stops
        
    def _generate_fare_stages(self, stops: List[Dict]) -> List[Dict]:
        """Generate fare stage information for the route."""
        fare_stages = []
        base_fare = 10.0  # Base fare in local currency
        
        for i in range(len(stops) - 1):
            from_stop = stops[i]
            to_stop = stops[i + 1]
            
            stage = {
                'stage_id': f"stage_{i+1}",
                'from_stop_name': from_stop.get('stop_name', ''),
                'to_stop_name': to_stop.get('stop_name', ''),
                'distance_km': 1.5,  # Estimated distance
                'fare_normal': base_fare + (i * 2),
                'fare_semi_luxury': (base_fare + (i * 2)) * 1.5,
                'fare_luxury': (base_fare + (i * 2)) * 2.0,
                'effective_from': '2025-07-04'
            }
            fare_stages.append(stage)
            
        return fare_stages
        
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
        
    def _save_enriched_data(self, data: List[Dict], output_path: str):
        """Save enriched data to file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.suffix.lower() == '.json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        elif output_path.suffix.lower() == '.csv':
            self._save_as_csv(data, output_path)
        else:
            raise ValueError(f"Unsupported output format: {output_path.suffix}")
            
        logger.info(f"Enriched data saved to {output_path}")
        
    def _save_as_csv(self, data: List[Dict], output_path: Path):
        """Save data as CSV file."""
        if not data:
            return
            
        # Flatten nested dictionaries for CSV
        flattened_data = []
        for item in data:
            flattened = self._flatten_dict(item)
            flattened_data.append(flattened)
            
        fieldnames = set()
        for item in flattened_data:
            fieldnames.update(item.keys())
            
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
            writer.writeheader()
            writer.writerows(flattened_data)
            
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '_') -> Dict:
        """Flatten nested dictionary for CSV export."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                items.append((new_key, json.dumps(v)))
            else:
                items.append((new_key, v))
        return dict(items)