#!/usr/bin/env python3
"""
Data Quality Checker
Validates data quality across the entire dataset pipeline.
"""

import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any
import jsonschema

logger = logging.getLogger(__name__)

class DataQualityChecker:
    """Comprehensive data quality validation."""
    
    def __init__(self, config_path: str = None):
        """Initialize quality checker with configuration."""
        self.base_path = Path(__file__).parent.parent.parent
        self.schemas_path = self.base_path / 'schemas'
        
        # Load schemas
        self.route_schema = self._load_schema('route_schema.json')
        self.stop_schema = self._load_schema('stop_schema.json')
        
    def _load_schema(self, schema_file: str) -> Dict:
        """Load JSON schema from file."""
        schema_path = self.schemas_path / schema_file
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def validate_routes_data(self, routes_data: List[Dict]) -> Dict[str, Any]:
        """
        Validate routes data against schema and business rules.
        
        Args:
            routes_data: List of route dictionaries
            
        Returns:
            Validation report dictionary
        """
        report = {
            'total_routes': len(routes_data),
            'valid_routes': 0,
            'invalid_routes': 0,
            'validation_errors': [],
            'quality_metrics': {},
            'recommendations': []
        }
        
        valid_routes = 0
        
        for i, route in enumerate(routes_data):
            try:
                # Schema validation
                jsonschema.validate(route, self.route_schema)
                
                # Business rule validation
                business_errors = self._validate_route_business_rules(route)
                
                if not business_errors:
                    valid_routes += 1
                else:
                    report['validation_errors'].extend([
                        f"Route {i+1} ({route.get('route_number', 'Unknown')}): {error}"
                        for error in business_errors
                    ])
                    
            except jsonschema.ValidationError as e:
                report['validation_errors'].append(
                    f"Route {i+1} schema error: {e.message}"
                )
                
        report['valid_routes'] = valid_routes
        report['invalid_routes'] = len(routes_data) - valid_routes
        
        # Calculate quality metrics
        report['quality_metrics'] = self._calculate_quality_metrics(routes_data)
        
        # Generate recommendations
        report['recommendations'] = self._generate_recommendations(report)
        
        return report
        
    def _validate_route_business_rules(self, route: Dict) -> List[str]:
        """Validate business rules for a single route."""
        errors = []
        
        # Check minimum stops
        stops = route.get('stops', [])
        if len(stops) < 2:
            errors.append("Route must have at least 2 stops")
            
        # Check stop sequence
        sequences = [stop.get('sequence', 0) for stop in stops if 'sequence' in stop]
        if sequences != sorted(sequences):
            errors.append("Stop sequences must be in ascending order")
            
        # Check fare stages consistency
        fare_stages = route.get('fare_stages', [])
        if len(stops) > 2 and len(fare_stages) == 0:
            errors.append("Routes with multiple stops should have fare stages")
            
        # Check route number format
        route_number = route.get('route_number', '')
        if not route_number or len(route_number) > 10:
            errors.append("Route number must be 1-10 characters")
            
        return errors
        
    def _calculate_quality_metrics(self, routes_data: List[Dict]) -> Dict[str, float]:
        """Calculate various quality metrics."""
        if not routes_data:
            return {}
            
        metrics = {}
        
        # Completeness metrics
        total_routes = len(routes_data)
        routes_with_coordinates = sum(1 for route in routes_data 
                                    if any(stop.get('latitude') and stop.get('longitude') 
                                          for stop in route.get('stops', [])))
        
        routes_with_fare_stages = sum(1 for route in routes_data 
                                    if route.get('fare_stages'))
        
        routes_with_multilingual_names = sum(1 for route in routes_data 
                                           if any(stop.get('stop_name_sinhala') 
                                                 for stop in route.get('stops', [])))
        
        metrics['coordinate_completeness'] = (routes_with_coordinates / total_routes) * 100
        metrics['fare_completeness'] = (routes_with_fare_stages / total_routes) * 100
        metrics['multilingual_completeness'] = (routes_with_multilingual_names / total_routes) * 100
        
        # Data consistency metrics
        all_stops = []
        for route in routes_data:
            all_stops.extend(route.get('stops', []))
            
        unique_stop_names = len(set(stop.get('stop_name', '') for stop in all_stops))
        total_stop_entries = len(all_stops)
        
        if total_stop_entries > 0:
            metrics['stop_name_uniqueness'] = (unique_stop_names / total_stop_entries) * 100
            
        # Route type distribution
        route_types = [route.get('route_type', 'REGULAR') for route in routes_data]
        metrics['regular_routes_percentage'] = (route_types.count('REGULAR') / total_routes) * 100
        
        return metrics
        
    def _generate_recommendations(self, report: Dict) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        metrics = report.get('quality_metrics', {})
        
        # Coordinate completeness
        coord_completeness = metrics.get('coordinate_completeness', 0)
        if coord_completeness < 50:
            recommendations.append(
                "Low coordinate completeness. Consider GPS survey or geocoding service."
            )
        elif coord_completeness < 80:
            recommendations.append(
                "Moderate coordinate completeness. Prioritize major routes for GPS data."
            )
            
        # Fare completeness
        fare_completeness = metrics.get('fare_completeness', 0)
        if fare_completeness < 70:
            recommendations.append(
                "Missing fare information for many routes. Update from official sources."
            )
            
        # Multilingual support
        multilingual_completeness = metrics.get('multilingual_completeness', 0)
        if multilingual_completeness < 30:
            recommendations.append(
                "Add Sinhala and Tamil translations for better accessibility."
            )
            
        # Validation errors
        error_count = len(report.get('validation_errors', []))
        if error_count > 0:
            recommendations.append(
                f"Fix {error_count} validation errors to improve data quality."
            )
            
        return recommendations
        
    def generate_quality_report(self, output_path: str = None) -> str:
        """Generate a comprehensive quality report."""
        # Load processed data
        processed_path = self.base_path / 'processed-data' / 'routes'
        
        routes_data = []
        for json_file in processed_path.glob('*.json'):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    routes_data.extend(data)
                else:
                    routes_data.append(data)
                    
        # Validate data
        validation_report = self.validate_routes_data(routes_data)
        
        # Generate report text
        report_lines = [
            "# BusMate Dataset Quality Report",
            f"Generated: {self._get_timestamp()}",
            "",
            "## Summary",
            f"- Total Routes: {validation_report['total_routes']}",
            f"- Valid Routes: {validation_report['valid_routes']}",
            f"- Invalid Routes: {validation_report['invalid_routes']}",
            f"- Success Rate: {(validation_report['valid_routes'] / max(validation_report['total_routes'], 1)) * 100:.1f}%",
            "",
            "## Quality Metrics"
        ]
        
        metrics = validation_report['quality_metrics']
        for metric, value in metrics.items():
            report_lines.append(f"- {metric.replace('_', ' ').title()}: {value:.1f}%")
            
        report_lines.extend([
            "",
            "## Validation Errors",
            ""
        ])
        
        errors = validation_report['validation_errors'][:10]  # Limit to first 10
        for error in errors:
            report_lines.append(f"- {error}")
            
        if len(validation_report['validation_errors']) > 10:
            remaining = len(validation_report['validation_errors']) - 10
            report_lines.append(f"- ... and {remaining} more errors")
            
        report_lines.extend([
            "",
            "## Recommendations",
            ""
        ])
        
        for recommendation in validation_report['recommendations']:
            report_lines.append(f"- {recommendation}")
            
        report_text = '\n'.join(report_lines)
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            logger.info(f"Quality report saved to {output_path}")
            
        return report_text
        
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


if __name__ == '__main__':
    """Run quality check from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Check BusMate dataset quality')
    parser.add_argument('--output', type=str, help='Output file for report')
    
    args = parser.parse_args()
    
    checker = DataQualityChecker()
    
    output_path = args.output or '../../logs/quality_reports/quality_report.md'
    report = checker.generate_quality_report(output_path)
    
    print("Quality Report Generated:")
    print("=" * 50)
    print(report)