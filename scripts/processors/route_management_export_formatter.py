#!/usr/bin/env python3
"""
Route Management Service Export Formatter
Creates exports compatible with Route Management Service API DTOs.
"""

import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class RouteManagementExportFormatter:
    """Formats data for Route Management Service API compatibility."""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize export formatter.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        
    def format_for_api_import(self, processed_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Format processed data for Route Management Service API import.
        
        Args:
            processed_data: Dictionary with entity lists
            
        Returns:
            Formatted data ready for API import
        """
        formatted_export = {
            "metadata": {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "1.0",
                "source": "busmate-dataset-pipeline",
                "total_entities": 0
            },
            "route_groups": [],
            "stops": [],
            "routes": [],
            "route_stops": []
        }
        
        # Format route groups
        if 'route_groups' in processed_data:
            formatted_export['route_groups'] = [
                self._format_route_group_for_api(rg) 
                for rg in processed_data['route_groups']
            ]
            
        # Format stops
        if 'stops' in processed_data:
            formatted_export['stops'] = [
                self._format_stop_for_api(stop) 
                for stop in processed_data['stops']
            ]
            
        # Format routes
        if 'routes' in processed_data:
            formatted_export['routes'] = [
                self._format_route_for_api(route) 
                for route in processed_data['routes']
            ]
            
        # Format route stops
        if 'route_stops' in processed_data:
            formatted_export['route_stops'] = [
                self._format_route_stop_for_api(rs) 
                for rs in processed_data['route_stops']
            ]
            
        # Update metadata
        formatted_export['metadata']['total_entities'] = (
            len(formatted_export['route_groups']) +
            len(formatted_export['stops']) +
            len(formatted_export['routes']) +
            len(formatted_export['route_stops'])
        )
        
        return formatted_export
        
    def _format_route_group_for_api(self, route_group: Dict) -> Dict:
        """Format route group for RouteGroupRequest DTO."""
        return {
            "name": route_group.get('name', '').strip(),
            "description": route_group.get('description', '').strip() or None
        }
        
    def _format_stop_for_api(self, stop: Dict) -> Dict:
        """Format stop for StopRequest DTO."""
        formatted_stop = {
            "name": stop.get('name', '').strip(),
            "description": stop.get('description', '').strip() or None,
            "isAccessible": stop.get('is_accessible', False)
        }
        
        # Handle location data
        location = stop.get('location', {})
        if location:
            formatted_stop["location"] = {
                "latitude": location.get('latitude'),
                "longitude": location.get('longitude'), 
                "address": location.get('address', '').strip() or None,
                "city": location.get('city', '').strip() or None,
                "state": location.get('state', '').strip() or None,
                "zipCode": location.get('zip_code', '').strip() or None,
                "country": location.get('country', 'Sri Lanka')
            }
            
            # Remove None values from location
            formatted_stop["location"] = {
                k: v for k, v in formatted_stop["location"].items() 
                if v is not None
            }
            
        return formatted_stop
        
    def _format_route_for_api(self, route: Dict) -> Dict:
        """Format route for RouteRequest DTO."""
        formatted_route = {
            "name": route.get('name', '').strip(),
            "description": route.get('description', '').strip() or None,
            "routeGroupId": route.get('route_group_id'),
            "startStopId": route.get('start_stop_id'), 
            "endStopId": route.get('end_stop_id'),
            "distanceKm": route.get('distance_km'),
            "estimatedDurationMinutes": route.get('estimated_duration_minutes'),
            "direction": route.get('direction')  # OUTBOUND/INBOUND
        }
        
        # Remove None values
        return {k: v for k, v in formatted_route.items() if v is not None}
        
    def _format_route_stop_for_api(self, route_stop: Dict) -> Dict:
        """Format route stop for RouteStopRequest DTO."""
        return {
            "routeId": route_stop.get('route_id'),
            "stopId": route_stop.get('stop_id'),
            "stopOrder": route_stop.get('stop_order'),
            "distanceFromStartKm": route_stop.get('distance_from_start_km')
        }
        
    def create_bulk_import_format(self, processed_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Create format for bulk import operations.
        
        Args:
            processed_data: Processed entity data
            
        Returns:
            Bulk import formatted data
        """
        bulk_format = {
            "import_metadata": {
                "import_id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": "dataset-pipeline",
                "validation_enabled": True
            },
            "entities": {}
        }
        
        # Process each entity type
        entity_order = ['route_groups', 'stops', 'routes', 'route_stops']
        
        for entity_type in entity_order:
            if entity_type in processed_data:
                bulk_format['entities'][entity_type] = {
                    "count": len(processed_data[entity_type]),
                    "data": processed_data[entity_type]
                }
                
        return bulk_format
        
    def create_mobile_app_export(self, processed_data: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """
        Create optimized export for mobile applications.
        
        Args:
            processed_data: Processed entity data
            
        Returns:
            Mobile-optimized data format
        """
        mobile_export = {
            "version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "routes": [],
            "stops": [],
            "route_stops_lookup": {}
        }
        
        # Simplified route format for mobile
        if 'routes' in processed_data:
            for route in processed_data['routes']:
                mobile_route = {
                    "id": route.get('id'),
                    "name": route.get('name'),
                    "direction": route.get('direction'),
                    "distance_km": route.get('distance_km'),
                    "duration_minutes": route.get('estimated_duration_minutes')
                }
                mobile_export['routes'].append(mobile_route)
                
        # Simplified stop format for mobile
        if 'stops' in processed_data:
            for stop in processed_data['stops']:
                location = stop.get('location', {})
                mobile_stop = {
                    "id": stop.get('id'),
                    "name": stop.get('name'),
                    "lat": location.get('latitude'),
                    "lng": location.get('longitude'),
                    "city": location.get('city')
                }
                # Remove None values
                mobile_stop = {k: v for k, v in mobile_stop.items() if v is not None}
                mobile_export['stops'].append(mobile_stop)
                
        # Create route-stops lookup for efficient mobile queries
        if 'route_stops' in processed_data:
            for route_stop in processed_data['route_stops']:
                route_id = route_stop.get('route_id')
                if route_id not in mobile_export['route_stops_lookup']:
                    mobile_export['route_stops_lookup'][route_id] = []
                    
                mobile_export['route_stops_lookup'][route_id].append({
                    "stop_id": route_stop.get('stop_id'),
                    "order": route_stop.get('stop_order'),
                    "distance_km": route_stop.get('distance_from_start_km')
                })
                
        # Sort route stops by order
        for route_id in mobile_export['route_stops_lookup']:
            mobile_export['route_stops_lookup'][route_id].sort(
                key=lambda x: x.get('order', 0)
            )
            
        return mobile_export
        
    def create_location_service_export(self, processed_data: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Create export for location tracking service.
        
        Args:
            processed_data: Processed entity data
            
        Returns:
            Location service compatible data
        """
        location_export = []
        
        # Create route-stop combinations for location tracking
        routes_lookup = {}
        if 'routes' in processed_data:
            routes_lookup = {r['id']: r for r in processed_data['routes']}
            
        stops_lookup = {}
        if 'stops' in processed_data:
            stops_lookup = {s['id']: s for s in processed_data['stops']}
            
        if 'route_stops' in processed_data:
            for route_stop in processed_data['route_stops']:
                route_id = route_stop.get('route_id')
                stop_id = route_stop.get('stop_id')
                
                route = routes_lookup.get(route_id, {})
                stop = stops_lookup.get(stop_id, {})
                stop_location = stop.get('location', {})
                
                if stop_location.get('latitude') and stop_location.get('longitude'):
                    location_record = {
                        "route_id": route_id,
                        "route_name": route.get('name'),
                        "stop_id": stop_id,
                        "stop_name": stop.get('name'),
                        "stop_order": route_stop.get('stop_order'),
                        "latitude": stop_location.get('latitude'),
                        "longitude": stop_location.get('longitude'),
                        "distance_from_start_km": route_stop.get('distance_from_start_km'),
                        "city": stop_location.get('city'),
                        "state": stop_location.get('state')
                    }
                    location_export.append(location_record)
                    
        # Sort by route and then by stop order
        location_export.sort(key=lambda x: (x['route_name'], x['stop_order']))
        
        return location_export
        
    def save_exports(self, processed_data: Dict[str, List[Dict]], output_dir: str):
        """
        Save all export formats to files.
        
        Args:
            processed_data: Processed entity data
            output_dir: Directory to save exports
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # API Import format
        api_export = self.format_for_api_import(processed_data)
        with open(output_path / 'route_management_api_import.json', 'w') as f:
            json.dump(api_export, f, indent=2, ensure_ascii=False)
            
        # Bulk import format
        bulk_export = self.create_bulk_import_format(processed_data)
        with open(output_path / 'bulk_import_format.json', 'w') as f:
            json.dump(bulk_export, f, indent=2, ensure_ascii=False)
            
        # Mobile app export
        mobile_export = self.create_mobile_app_export(processed_data)
        with open(output_path / 'mobile_app_export.json', 'w') as f:
            json.dump(mobile_export, f, indent=2, ensure_ascii=False)
            
        # Location service export
        location_export = self.create_location_service_export(processed_data)
        with open(output_path / 'location_service_export.json', 'w') as f:
            json.dump(location_export, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Exported data to {output_path}")
        
        return {
            'api_import': len(api_export.get('routes', [])),
            'bulk_import': len(bulk_export.get('entities', {})),
            'mobile_export': len(mobile_export.get('routes', [])),
            'location_export': len(location_export)
        }