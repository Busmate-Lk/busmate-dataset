#!/usr/bin/env python3
"""
Full Data Processing Pipeline
Orchestrates the complete data processing workflow from raw PDF to final exports.
"""

import os
import sys
import logging
import yaml
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../../logs/pipeline_runs/full_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataProcessingPipeline:
    """Complete data processing pipeline for BusMate dataset."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the processing pipeline.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or '../../config/settings.yaml'
        self.config = self._load_config()
        
        # Initialize processors
        self.pdf_extractor = PDFExtractor(self.config.get('processing', {}))
        self.text_cleaner = TextCleaner(self.config.get('processing', {}))
        self.route_parser = None  # Will be initialized when needed
        self.stop_validator = StopValidator(self.config.get('quality', {}))
        self.data_enricher = DataEnricher(self.config.get('pipeline', {}).get('enrichment', {}))
        
        # Set up paths
        self.base_path = Path(__file__).parent.parent.parent
        self.raw_data_path = self.base_path / self.config['paths']['raw_data']
        self.staging_path = self.base_path / self.config['paths']['staging']
        self.processed_path = self.base_path / self.config['paths']['processed_data']
        self.exports_path = self.base_path / self.config['paths']['exports']
        
    def run_full_pipeline(self, source_pdf: Optional[str] = None) -> Dict:
        """
        Execute the complete data processing pipeline.
        
        Args:
            source_pdf: Path to source PDF file (optional, will find automatically if not provided)
            
        Returns:
            Dictionary containing pipeline execution results
        """
        logger.info("Starting full data processing pipeline")
        start_time = datetime.now()
        
        results = {
            'status': 'started',
            'start_time': start_time.isoformat(),
            'stages': {}
        }
        
        try:
            # Stage 1: PDF Extraction
            logger.info("Stage 1: PDF Extraction")
            if not source_pdf:
                source_pdf = self._find_source_pdf()
            
            extracted_text = self._stage_1_extraction(source_pdf)
            results['stages']['extraction'] = {'status': 'completed', 'output_length': len(extracted_text)}
            
            # Stage 2: Text Cleaning
            logger.info("Stage 2: Text Cleaning")
            cleaned_text = self._stage_2_cleaning(extracted_text)
            results['stages']['cleaning'] = {'status': 'completed', 'output_length': len(cleaned_text)}
            
            # Stage 3: Route Parsing
            logger.info("Stage 3: Route Parsing")
            structured_routes = self._stage_3_structuring(cleaned_text)
            results['stages']['structuring'] = {'status': 'completed', 'routes_parsed': len(structured_routes)}
            
            # Stage 4: Data Validation
            logger.info("Stage 4: Data Validation")
            validated_data = self._stage_4_validation(structured_routes)
            results['stages']['validation'] = {'status': 'completed', 'valid_routes': len(validated_data)}
            
            # Stage 5: Data Enrichment
            logger.info("Stage 5: Data Enrichment")
            enriched_data = self._stage_5_enrichment(validated_data)
            results['stages']['enrichment'] = {'status': 'completed', 'enriched_routes': len(enriched_data)}
            
            # Stage 6: Export Generation
            logger.info("Stage 6: Export Generation")
            export_results = self._generate_exports(enriched_data)
            results['stages']['exports'] = export_results
            
            # Final results
            end_time = datetime.now()
            results.update({
                'status': 'completed',
                'end_time': end_time.isoformat(),
                'duration_seconds': (end_time - start_time).total_seconds(),
                'total_routes_processed': len(enriched_data)
            })
            
            logger.info(f"Pipeline completed successfully in {results['duration_seconds']:.2f} seconds")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            results.update({
                'status': 'failed',
                'error': str(e),
                'end_time': datetime.now().isoformat()
            })
            raise
            
        return results
        
    def _load_config(self) -> Dict:
        """Load configuration from YAML file."""
        config_path = Path(self.config_path)
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._get_default_config()
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            'paths': {
                'raw_data': 'raw-data/',
                'staging': 'staging/',
                'processed_data': 'processed-data/',
                'exports': 'exports/'
            },
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
        """Find the source PDF file automatically."""
        pdf_dir = self.raw_data_path / 'sources' / 'ntc-pdf'
        pdf_files = list(pdf_dir.glob('*.pdf'))
        
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files found in {pdf_dir}")
            
        if len(pdf_files) > 1:
            logger.warning(f"Multiple PDF files found, using the first: {pdf_files[0]}")
            
        return str(pdf_files[0])
        
    def _stage_1_extraction(self, pdf_path: str) -> str:
        """Stage 1: Extract text from PDF."""
        output_path = self.staging_path / 'step-1-extraction' / 'raw_pdf_content.txt'
        return self.pdf_extractor.extract_text(pdf_path, str(output_path))
        
    def _stage_2_cleaning(self, text: str) -> str:
        """Stage 2: Clean extracted text."""
        output_path = self.staging_path / 'step-2-cleaning' / 'cleaned_content.txt'
        return self.text_cleaner.clean_text(text, str(output_path))
        
    def _stage_3_structuring(self, text: str) -> List[Dict]:
        """Stage 3: Parse routes from cleaned text."""
        # Initialize route parser with staging paths
        input_file = self.staging_path / 'step-2-cleaning' / 'cleaned_content.txt'
        output_file = self.staging_path / 'step-3-structuring' / 'parsed_routes.csv'
        
        # Write text to input file for parser
        with open(input_file, 'w', encoding='utf-8') as f:
            f.write(text)
            
        self.route_parser = BusRouteParser(str(input_file), str(output_file))
        return self.route_parser.parse_route_data()
        
    def _stage_4_validation(self, routes: List[Dict]) -> List[Dict]:
        """Stage 4: Validate route and stop data."""
        return self.stop_validator.validate_routes(routes)
        
    def _stage_5_enrichment(self, routes: List[Dict]) -> List[Dict]:
        """Stage 5: Enrich data with additional information."""
        output_path = self.staging_path / 'step-5-enrichment' / 'enriched_routes.json'
        return self.data_enricher.enrich_routes(routes, str(output_path))
        
    def _generate_exports(self, enriched_data: List[Dict]) -> Dict:
        """Generate exports for different services."""
        export_results = {}
        
        # Mobile app export
        mobile_export = self._create_mobile_export(enriched_data)
        mobile_path = self.exports_path / 'mobile-app' / 'routes.json'
        self._save_export(mobile_export, mobile_path)
        export_results['mobile_app'] = {'status': 'completed', 'file': str(mobile_path)}
        
        # Web frontend export
        web_export = self._create_web_export(enriched_data)
        web_path = self.exports_path / 'web-frontend' / 'routes.json'
        self._save_export(web_export, web_path)
        export_results['web_frontend'] = {'status': 'completed', 'file': str(web_path)}
        
        # Location service export
        location_export = self._create_location_export(enriched_data)
        location_path = self.exports_path / 'location-service' / 'routes.csv'
        self._save_export_csv(location_export, location_path)
        export_results['location_service'] = {'status': 'completed', 'file': str(location_path)}
        
        # Route management service export
        route_export = self._create_route_service_export(enriched_data)
        route_path = self.exports_path / 'route-service' / 'routes.json'
        self._save_export(route_export, route_path)
        export_results['route_service'] = {'status': 'completed', 'file': str(route_path)}
        
        return export_results
        
    def _create_mobile_export(self, data: List[Dict]) -> Dict:
        """Create export format for mobile app."""
        mobile_routes = []
        for route in data:
            mobile_route = {
                'route_id': route.get('route_id'),
                'route_number': route.get('route_number'),
                'route_name': route.get('route_name'),
                'operator': route.get('operator'),
                'stops': [stop.get('stop_name') for stop in route.get('stops', [])],
                'status': route.get('status', 'ACTIVE')
            }
            mobile_routes.append(mobile_route)
            
        return {
            'routes': mobile_routes,
            'total_count': len(mobile_routes),
            'last_updated': datetime.now().isoformat(),
            'version': '1.0'
        }
        
    def _create_web_export(self, data: List[Dict]) -> Dict:
        """Create export format for web frontend."""
        return {
            'routes': data,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_routes': len(data),
                'data_source': 'ntc_pdf_processing',
                'version': '1.0'
            }
        }
        
    def _create_location_export(self, data: List[Dict]) -> List[Dict]:
        """Create CSV export for location service."""
        csv_data = []
        for route in data:
            for stop in route.get('stops', []):
                csv_data.append({
                    'route_id': route.get('route_id'),
                    'route_number': route.get('route_number'),
                    'stop_name': stop.get('stop_name'),
                    'stop_sequence': stop.get('sequence', 0),
                    'latitude': stop.get('latitude', ''),
                    'longitude': stop.get('longitude', '')
                })
        return csv_data
        
    def _create_route_service_export(self, data: List[Dict]) -> List[Dict]:
        """Create export format for route management service."""
        return data  # Full data for route management service
        
    def _save_export(self, data: Dict, file_path: Path):
        """Save export data as JSON."""
        import json
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def _save_export_csv(self, data: List[Dict], file_path: Path):
        """Save export data as CSV."""
        import csv
        if not data:
            return
            
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)


if __name__ == '__main__':
    """Run the pipeline from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run BusMate data processing pipeline')
    parser.add_argument('--pdf', type=str, help='Path to source PDF file')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    
    args = parser.parse_args()
    
    pipeline = DataProcessingPipeline(config_path=args.config)
    results = pipeline.run_full_pipeline(source_pdf=args.pdf)
    
    print(f"Pipeline completed with status: {results['status']}")
    if results['status'] == 'completed':
        print(f"Processed {results['total_routes_processed']} routes in {results['duration_seconds']:.2f} seconds")
    else:
        print(f"Error: {results.get('error', 'Unknown error')}")