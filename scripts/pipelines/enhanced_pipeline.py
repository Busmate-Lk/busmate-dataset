#!/usr/bin/env python3
"""
Enhanced Full Data Processing Pipeline
Orchestrates the complete data processing workflow aligned with Route Management Service.
"""

import os
import sys
import json
import yaml
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add the processors directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'processors'))

from pdf_extractor import PDFExtractor
from text_cleaner import TextCleaner
from route_parser import BusRouteParser
from stop_validator import StopValidator
from data_enricher import DataEnricher
from route_management_export_formatter import RouteManagementExportFormatter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../../logs/pipeline_runs/enhanced_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedDataProcessingPipeline:
    """Enhanced data processing pipeline for Route Management Service integration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize pipeline with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.base_path = Path(__file__).parent.parent.parent
        self.config = self._load_config(config_path)
        self.db_mapping = self._load_database_mapping()
        
        # Initialize processors
        self.pdf_extractor = PDFExtractor(self.config.get('processing', {}))
        self.text_cleaner = TextCleaner(self.config.get('processing', {}))
        self.route_parser = BusRouteParser(self.config.get('processing', {}))
        self.stop_validator = StopValidator(self.config.get('quality', {}))
        self.data_enricher = DataEnricher(self.config.get('processing', {}))
        self.export_formatter = RouteManagementExportFormatter()
        
    def run_enhanced_pipeline(self, source_pdf: Optional[str] = None) -> Dict:
        """
        Run the complete enhanced pipeline.
        
        Args:
            source_pdf: Optional path to source PDF file
            
        Returns:
            Pipeline execution results
        """
        pipeline_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        results = {
            'pipeline_id': pipeline_id,
            'start_time': start_time.isoformat(),
            'stages': {},
            'entities_created': {},
            'export_formats': {},
            'errors': [],
            'success': False
        }
        
        try:
            logger.info(f"Starting enhanced pipeline {pipeline_id}")
            
            # Stage 1: PDF Extraction
            logger.info("Stage 1: PDF Extraction")
            pdf_path = source_pdf or self._find_source_pdf()
            extracted_text = self._stage_1_extraction(pdf_path)
            results['stages']['extraction'] = {'status': 'completed', 'output_length': len(extracted_text)}
            
            # Stage 2: Text Cleaning
            logger.info("Stage 2: Text Cleaning")
            cleaned_text = self._stage_2_cleaning(extracted_text)
            results['stages']['cleaning'] = {'status': 'completed', 'output_length': len(cleaned_text)}
            
            # Stage 3: Route Parsing
            logger.info("Stage 3: Route Parsing")
            raw_routes = self._stage_3_parsing(cleaned_text)
            results['stages']['parsing'] = {'status': 'completed', 'routes_found': len(raw_routes)}
            
            # Stage 4: Entity Creation
            logger.info("Stage 4: Entity Creation")
            entities = self._stage_4_entity_creation(raw_routes)
            results['stages']['entity_creation'] = {'status': 'completed'}
            results['entities_created'] = {
                'route_groups': len(entities['route_groups']),
                'stops': len(entities['stops']),
                'routes': len(entities['routes']),
                'route_stops': len(entities['route_stops'])
            }
            
            # Stage 5: Validation
            logger.info("Stage 5: Validation")
            validated_entities = self._stage_5_validation(entities)
            results['stages']['validation'] = {'status': 'completed'}
            
            # Stage 6: Enrichment
            logger.info("Stage 6: Enrichment")
            enriched_entities = self._stage_6_enrichment(validated_entities)
            results['stages']['enrichment'] = {'status': 'completed'}
            
            # Stage 7: Export Generation
            logger.info("Stage 7: Export Generation")
            export_results = self._stage_7_export_generation(enriched_entities)
            results['stages']['export_generation'] = {'status': 'completed'}
            results['export_formats'] = export_results
            
            results['success'] = True
            results['end_time'] = datetime.now().isoformat()
            
            logger.info(f"Pipeline {pipeline_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Pipeline {pipeline_id} failed: {e}")
            results['errors'].append(str(e))
            results['success'] = False
            results['end_time'] = datetime.now().isoformat()
            
        return results
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from file."""
        if config_path is None:
            config_path = self.base_path / 'config' / 'settings.yaml'
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning("Configuration file not found, using defaults")
            return self._get_default_config()
            
    def _load_database_mapping(self) -> Dict:
        """Load database mapping configuration."""
        try:
            mapping_path = self.base_path / 'config' / 'database_mapping.yaml'
            with open(mapping_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning("Database mapping file not found")
            return {}
            
    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            'processing': {
                'batch_size': 1000,
                'remove_duplicates': True,
                'normalize_text': True
            },
            'quality': {
                'min_route_stops': 2,
                'max_route_stops': 100
            }
        }
        
    def _find_source_pdf(self) -> str:
        """Find source PDF file."""
        pdf_dir = self.base_path / 'raw-data' / 'sources' / 'ntc-pdf'
        pdf_files = list(pdf_dir.glob('*.pdf'))
        
        if not pdf_files:
            raise FileNotFoundError("No PDF files found in raw data directory")
            
        return str(pdf_files[0])  # Use first PDF found
        
    def _stage_1_extraction(self, pdf_path: str) -> str:
        """Extract text from PDF."""
        return self.pdf_extractor.extract_text(pdf_path)
        
    def _stage_2_cleaning(self, text: str) -> str:
        """Clean extracted text."""
        return self.text_cleaner.clean_text(text)
        
    def _stage_3_parsing(self, text: str) -> List[Dict]:
        """Parse routes from cleaned text."""
        return self.route_parser.parse_routes_from_text(text)
        
    def _stage_4_entity_creation(self, raw_routes: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Create entities aligned with Route Management Service.
        
        Args:
            raw_routes: Raw route data from parsing
            
        Returns:
            Dictionary with entity lists
        """
        entities = {
            'route_groups': [],
            'stops': [],
            'routes': [],
            'route_stops': []
        }
        
        # Create stops lookup
        stops_lookup = {}
        
        # Process each raw route
        for raw_route in raw_routes:
            # Create route group (simplified - one group per route for now)
            route_group = self._create_route_group(raw_route)
            entities['route_groups'].append(route_group)
            
            # Extract and create stops
            route_stops_data = []
            if 'stops' in raw_route:
                for i, stop_data in enumerate(raw_route['stops'], 1):
                    # Create or get existing stop
                    stop = self._create_or_get_stop(stop_data, stops_lookup)
                    if stop['id'] not in stops_lookup:
                        entities['stops'].append(stop)
                        stops_lookup[stop['id']] = stop
                        
                    # Create route-stop relationship
                    route_stop = self._create_route_stop(
                        route_id=None,  # Will be set when route is created
                        stop_id=stop['id'],
                        stop_order=i,
                        distance_km=stop_data.get('distance_km', 0)
                    )
                    route_stops_data.append(route_stop)
                    
            # Create route
            route = self._create_route(raw_route, route_group['id'], route_stops_data)
            entities['routes'].append(route)
            
            # Update route_stops with actual route_id
            for route_stop in route_stops_data:
                route_stop['route_id'] = route['id']
                entities['route_stops'].append(route_stop)
                
        return entities
        
    def _create_route_group(self, raw_route: Dict) -> Dict:
        """Create RouteGroup entity."""
        return {
            'id': str(uuid.uuid4()),
            'name': raw_route.get('route_name', f"Route {raw_route.get('route_number', 'Unknown')}"),
            'description': f"Route group for {raw_route.get('route_number', 'Unknown')}",
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'created_by': 'dataset-pipeline',
            'updated_by': 'dataset-pipeline'
        }
        
    def _create_or_get_stop(self, stop_data: Dict, stops_lookup: Dict) -> Dict:
        """Create or retrieve existing Stop entity."""
        stop_name = stop_data.get('stop_name', '').strip()
        
        # Check if stop already exists (simple name-based matching)
        for existing_stop in stops_lookup.values():
            if existing_stop['name'].lower() == stop_name.lower():
                return existing_stop
                
        # Create new stop
        stop_id = str(uuid.uuid4())
        return {
            'id': stop_id,
            'name': stop_name,
            'description': f"Bus stop: {stop_name}",
            'location': {
                'latitude': stop_data.get('latitude'),
                'longitude': stop_data.get('longitude'),
                'address': stop_data.get('address'),
                'city': stop_data.get('city'),
                'state': stop_data.get('district'),
                'country': 'Sri Lanka'
            },
            'is_accessible': False,  # Default value
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'created_by': 'dataset-pipeline',
            'updated_by': 'dataset-pipeline'
        }
        
    def _create_route(self, raw_route: Dict, route_group_id: str, route_stops: List[Dict]) -> Dict:
        """Create Route entity."""
        route_id = str(uuid.uuid4())
        
        # Determine start and end stops
        start_stop_id = route_stops[0]['stop_id'] if route_stops else None
        end_stop_id = route_stops[-1]['stop_id'] if route_stops else None
        
        return {
            'id': route_id,
            'name': raw_route.get('route_name', f"Route {raw_route.get('route_number', 'Unknown')}"),
            'description': raw_route.get('description'),
            'route_group_id': route_group_id,
            'start_stop_id': start_stop_id,
            'end_stop_id': end_stop_id,
            'distance_km': raw_route.get('total_distance_km'),
            'estimated_duration_minutes': raw_route.get('estimated_duration_minutes'),
            'direction': 'OUTBOUND',  # Default
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'created_by': 'dataset-pipeline',
            'updated_by': 'dataset-pipeline'
        }
        
    def _create_route_stop(self, route_id: Optional[str], stop_id: str, 
                          stop_order: int, distance_km: float) -> Dict:
        """Create RouteStop entity."""
        return {
            'id': str(uuid.uuid4()),
            'route_id': route_id,
            'stop_id': stop_id,
            'stop_order': stop_order,
            'distance_from_start_km': distance_km
        }
        
    def _stage_5_validation(self, entities: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Validate entity data."""
        # For now, pass through - validation can be enhanced
        return entities
        
    def _stage_6_enrichment(self, entities: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Enrich entity data."""
        # For now, pass through - enrichment can be enhanced
        return entities
        
    def _stage_7_export_generation(self, entities: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Generate various export formats."""
        exports_dir = self.base_path / 'exports'
        
        # Save individual entity files
        for entity_type, entity_data in entities.items():
            entity_file = exports_dir / f"{entity_type}.json"
            entity_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(entity_file, 'w', encoding='utf-8') as f:
                json.dump(entity_data, f, indent=2, ensure_ascii=False)
                
        # Generate service-specific exports
        export_results = self.export_formatter.save_exports(entities, str(exports_dir / 'route-management-service'))
        
        return export_results


def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run enhanced data processing pipeline')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--source-pdf', help='Source PDF file path')
    parser.add_argument('--output-dir', help='Output directory for results')
    
    args = parser.parse_args()
    
    # Setup pipeline
    pipeline = EnhancedDataProcessingPipeline(args.config)
    
    # Run pipeline
    logger.info("Starting enhanced data processing pipeline...")
    results = pipeline.run_enhanced_pipeline(args.source_pdf)
    
    # Save results
    if args.output_dir:
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results_file = output_path / 'pipeline_results.json'
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
    # Print summary
    print("\n=== Enhanced Pipeline Results ===")
    print(f"Pipeline ID: {results['pipeline_id']}")
    print(f"Success: {results['success']}")
    print(f"Start Time: {results['start_time']}")
    print(f"End Time: {results.get('end_time', 'N/A')}")
    
    if results['entities_created']:
        print("\nEntities Created:")
        for entity_type, count in results['entities_created'].items():
            print(f"  {entity_type}: {count}")
            
    if results['export_formats']:
        print(f"\nExport Formats Generated: {len(results['export_formats'])}")
        
    if results['errors']:
        print(f"\nErrors: {results['errors']}")
        
    print("\n=== Pipeline Complete ===")


if __name__ == '__main__':
    main()