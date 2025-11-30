#!/usr/bin/env python3
"""
Route Management Service Database Importer
Imports processed data into the Route Management Service PostgreSQL database.
"""

import os
import sys
import json
import yaml
import logging
import uuid
import psycopg2
from psycopg2.extras import execute_batch
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

# Add the processors directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'processors'))

logger = logging.getLogger(__name__)

class RouteManagementImporter:
    """Imports processed data into Route Management Service database."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize importer with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.base_path = Path(__file__).parent.parent.parent
        self.config = self._load_config(config_path)
        self.db_mapping = self._load_database_mapping()
        self.connection = None
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """Load configuration from file."""
        if config_path is None:
            config_path = self.base_path / 'config' / 'settings.yaml'
            
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def _load_database_mapping(self) -> Dict:
        """Load database mapping configuration."""
        mapping_path = self.base_path / 'config' / 'database_mapping.yaml'
        with open(mapping_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
            
    def connect_database(self, connection_params: Dict[str, str]):
        """
        Connect to PostgreSQL database.
        
        Args:
            connection_params: Database connection parameters
        """
        try:
            self.connection = psycopg2.connect(**connection_params)
            self.connection.autocommit = False
            logger.info("Connected to Route Management Service database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def import_processed_data(self, data_path: str) -> Dict[str, Any]:
        """
        Import all processed data from the specified path.
        
        Args:
            data_path: Path to processed data directory
            
        Returns:
            Import results summary
        """
        results = {
            'imported_entities': {},
            'errors': [],
            'total_records': 0,
            'successful_imports': 0,
            'failed_imports': 0
        }
        
        if not self.connection:
            raise RuntimeError("Database connection not established")
            
        try:
            # Import in order based on dependencies
            import_order = self.db_mapping['import']['import_order']
            
            for entity_type in import_order:
                logger.info(f"Importing {entity_type} data...")
                
                entity_results = self._import_entity_data(
                    entity_type, 
                    Path(data_path) / f"{entity_type}s.json"
                )
                
                results['imported_entities'][entity_type] = entity_results
                results['total_records'] += entity_results['total_records']
                results['successful_imports'] += entity_results['successful_imports']
                results['failed_imports'] += entity_results['failed_imports']
                
            # Commit all changes
            self.connection.commit()
            logger.info("Import completed successfully")
            
        except Exception as e:
            self.connection.rollback()
            logger.error(f"Import failed: {e}")
            results['errors'].append(str(e))
            raise
            
        return results
        
    def _import_entity_data(self, entity_type: str, data_file: Path) -> Dict[str, Any]:
        """Import data for a specific entity type."""
        results = {
            'entity_type': entity_type,
            'total_records': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'errors': []
        }
        
        if not data_file.exists():
            logger.warning(f"Data file not found: {data_file}")
            return results
            
        # Load data
        with open(data_file, 'r', encoding='utf-8') as f:
            data_records = json.load(f)
            
        if not isinstance(data_records, list):
            data_records = [data_records]
            
        results['total_records'] = len(data_records)
        
        # Get entity mapping
        entity_config = self.db_mapping['entities'][entity_type]
        table_name = entity_config['table_name']
        field_mappings = entity_config['fields']
        
        # Process records in batches
        batch_size = self.db_mapping['import']['batch_size']
        
        for i in range(0, len(data_records), batch_size):
            batch = data_records[i:i + batch_size]
            
            try:
                self._import_batch(entity_type, table_name, field_mappings, batch)
                results['successful_imports'] += len(batch)
                
            except Exception as e:
                logger.error(f"Batch import failed for {entity_type}: {e}")
                results['failed_imports'] += len(batch)
                results['errors'].append(f"Batch {i//batch_size + 1}: {str(e)}")
                
        return results
        
    def _import_batch(self, entity_type: str, table_name: str, 
                      field_mappings: Dict[str, str], batch: List[Dict]):
        """Import a batch of records for an entity."""
        
        # Prepare SQL statement
        columns = list(field_mappings.values())
        placeholders = ', '.join(['%s'] * len(columns))
        
        sql = f"""
            INSERT INTO {table_name} ({', '.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT (id) DO NOTHING
        """
        
        # Prepare data tuples
        data_tuples = []
        defaults = self.db_mapping['import'].get('defaults', {})
        
        for record in batch:
            # Transform record according to field mappings
            values = []
            
            for json_field, db_field in field_mappings.items():
                if json_field in record:
                    value = record[json_field]
                    
                    # Handle embedded objects (e.g., location.latitude)
                    if '.' in json_field:
                        parts = json_field.split('.')
                        temp_value = record
                        for part in parts:
                            temp_value = temp_value.get(part) if temp_value else None
                        value = temp_value
                        
                elif json_field in defaults:
                    value = defaults[json_field]
                    
                elif json_field in ['created_at', 'updated_at']:
                    value = datetime.now()
                    
                elif json_field == 'id' and not record.get('id'):
                    value = str(uuid.uuid4())
                    
                else:
                    value = None
                    
                values.append(value)
                
            data_tuples.append(tuple(values))
            
        # Execute batch insert
        with self.connection.cursor() as cursor:
            execute_batch(cursor, sql, data_tuples, page_size=100)
            
    def import_from_csv(self, csv_file: str, entity_type: str) -> Dict[str, Any]:
        """
        Import data from CSV file.
        
        Args:
            csv_file: Path to CSV file
            entity_type: Type of entity (stop, route, etc.)
            
        Returns:
            Import results
        """
        # This method can be implemented for direct CSV imports
        # For now, it's a placeholder
        logger.info(f"CSV import for {entity_type} from {csv_file} not yet implemented")
        return {'status': 'not_implemented'}
        
    def validate_data_integrity(self) -> Dict[str, Any]:
        """
        Validate data integrity after import.
        
        Returns:
            Validation results
        """
        validation_results = {
            'foreign_key_violations': [],
            'constraint_violations': [],
            'data_quality_issues': []
        }
        
        if not self.connection:
            raise RuntimeError("Database connection not established")
            
        try:
            with self.connection.cursor() as cursor:
                # Check foreign key constraints
                
                # 1. Routes should have valid route_group_id
                cursor.execute("""
                    SELECT r.id, r.name 
                    FROM route r 
                    LEFT JOIN route_group rg ON r.route_group_id = rg.id 
                    WHERE r.route_group_id IS NOT NULL AND rg.id IS NULL
                """)
                invalid_route_groups = cursor.fetchall()
                if invalid_route_groups:
                    validation_results['foreign_key_violations'].extend([
                        f"Route {name} (ID: {rid}) has invalid route_group_id"
                        for rid, name in invalid_route_groups
                    ])
                    
                # 2. RouteStops should have valid route_id and stop_id
                cursor.execute("""
                    SELECT rs.id 
                    FROM route_stop rs 
                    LEFT JOIN route r ON rs.route_id = r.id 
                    WHERE r.id IS NULL
                """)
                invalid_route_stops = cursor.fetchall()
                if invalid_route_stops:
                    validation_results['foreign_key_violations'].extend([
                        f"RouteStop {rsid} has invalid route_id"
                        for (rsid,) in invalid_route_stops
                    ])
                    
                # 3. Check stop ordering within routes
                cursor.execute("""
                    SELECT route_id, COUNT(*) as stop_count, 
                           MAX(stop_order) as max_order, 
                           COUNT(DISTINCT stop_order) as unique_orders
                    FROM route_stop 
                    GROUP BY route_id 
                    HAVING COUNT(*) != COUNT(DISTINCT stop_order)
                """)
                duplicate_orders = cursor.fetchall()
                if duplicate_orders:
                    validation_results['data_quality_issues'].extend([
                        f"Route {route_id} has duplicate stop orders"
                        for route_id, _, _, _ in duplicate_orders
                    ])
                    
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            validation_results['errors'] = [str(e)]
            
        return validation_results
        
    def close_connection(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")


def main():
    """Main function for command line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import data to Route Management Service')
    parser.add_argument('--data-path', required=True, help='Path to processed data directory')
    parser.add_argument('--db-host', default='localhost', help='Database host')
    parser.add_argument('--db-port', default='5432', help='Database port')
    parser.add_argument('--db-name', required=True, help='Database name')
    parser.add_argument('--db-user', required=True, help='Database user')
    parser.add_argument('--db-password', required=True, help='Database password')
    parser.add_argument('--validate', action='store_true', help='Validate data after import')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup importer
    importer = RouteManagementImporter()
    
    # Database connection parameters
    db_params = {
        'host': args.db_host,
        'port': args.db_port,
        'database': args.db_name,
        'user': args.db_user,
        'password': args.db_password
    }
    
    try:
        # Connect to database
        importer.connect_database(db_params)
        
        # Import data
        logger.info("Starting data import...")
        results = importer.import_processed_data(args.data_path)
        
        # Print results
        print("\n=== Import Results ===")
        print(f"Total records: {results['total_records']}")
        print(f"Successfully imported: {results['successful_imports']}")
        print(f"Failed imports: {results['failed_imports']}")
        
        for entity_type, entity_results in results['imported_entities'].items():
            print(f"\n{entity_type}:")
            print(f"  Records: {entity_results['total_records']}")
            print(f"  Success: {entity_results['successful_imports']}")
            print(f"  Failed: {entity_results['failed_imports']}")
            
        if results['errors']:
            print(f"\nErrors: {results['errors']}")
            
        # Validate if requested
        if args.validate:
            logger.info("Running data validation...")
            validation = importer.validate_data_integrity()
            
            print("\n=== Validation Results ===")
            if validation['foreign_key_violations']:
                print("Foreign Key Violations:")
                for violation in validation['foreign_key_violations']:
                    print(f"  - {violation}")
                    
            if validation['data_quality_issues']:
                print("Data Quality Issues:")
                for issue in validation['data_quality_issues']:
                    print(f"  - {issue}")
                    
            if not validation['foreign_key_violations'] and not validation['data_quality_issues']:
                print("✅ All validations passed!")
                
    except Exception as e:
        logger.error(f"Import failed: {e}")
        sys.exit(1)
        
    finally:
        importer.close_connection()


if __name__ == '__main__':
    main()