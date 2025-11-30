# Processing Pipeline Documentation

### Stage 1: PDF Extraction

**Purpose**: Extract text content from PDF documents  
**Input**: PDF files in `raw-data/sources/ntc-pdf/`  
**Output**: Plain text in `staging/step-1-extraction/`  
**Tools**: PyPDF2, pdfplumber  

**Common Issues**:
- OCR quality problems
- Unicode encoding issues
- Table structure preservation

### Stage 2: Text Cleaning

**Purpose**: Normalize and clean extracted text  
**Input**: Raw text from Stage 1  
**Output**: Cleaned text in `staging/step-2-cleaning/`  
**Processing**:
- Fix encoding issues
- Remove duplicates
- Normalize whitespace
- Handle Sinhala/Tamil text

### Stage 3: Data Structuring

**Purpose**: Parse text into structured route data  
**Input**: Cleaned text from Stage 2  
**Output**: Initial CSV/JSON in `staging/step-3-structuring/`  
**Logic**:
- Identify route sections
- Extract route numbers and names
- Parse stop sequences
- Extract operator information

### Stage 4: Data Validation

**Purpose**: Validate and correct parsed data  
**Input**: Structured data from Stage 3  
**Output**: Validated data in `staging/step-4-validation/`  
**Checks**:
- Route number formats
- Stop name consistency
- Sequence validation
- Duplicate detection

### Stage 5: Data Enrichment

**Purpose**: Add metadata and calculated fields  
**Input**: Validated data from Stage 4  
**Output**: Enriched data in `staging/step-5-enrichment/`  
**Additions**:
- Confidence scores
- Route classifications
- Distance calculations
- Fare stage generation

## API Integration Guide

### Mobile Application Integration

**Endpoint Format**: `/api/v1/routes/mobile`  
**Method**: GET  
**Response Format**: Compressed JSON  
**Update Frequency**: Daily  

**Sample Request**:
```bash
curl -H "Accept: application/json" \
     -H "Accept-Encoding: gzip" \
     https://api.busmate.lk/v1/routes/mobile
```

**Sample Response**:
```json
{
  "routes": [...],
  "metadata": {
    "last_updated": "2025-12-01T10:30:00Z",
    "total_routes": 150,
    "version": "1.0.0"
  }
}
```

### Web Frontend Integration

**Endpoint Format**: `/api/v1/routes/web`  
**Method**: GET  
**Response Format**: Full JSON with metadata  
**Update Frequency**: Real-time  

**Query Parameters**:
- `route_number`: Filter by route number
- `operator`: Filter by operator
- `district`: Filter by district
- `limit`: Limit results (default: 50)
- `offset`: Pagination offset

### Location Service Integration

**Endpoint Format**: `/api/v1/routes/locations`  
**Method**: GET  
**Response Format**: CSV or JSON  
**Update Frequency**: On-demand  

**Use Cases**:
- Real-time bus tracking
- Route optimization
- Stop coordinate updates

### Route Management Service Integration

**Endpoint Format**: `/api/v1/routes/management`  
**Methods**: GET, POST, PUT, DELETE  
**Response Format**: Complete route data  
**Authentication**: Required  

**Operations**:
- Create new routes
- Update existing routes
- Manage route schedules
- Bulk operations

## Troubleshooting Guide

### Common Processing Issues

#### 1. PDF Extraction Failures

**Symptoms**:
- Empty text output
- Garbled characters
- Missing content

**Solutions**:
```bash
# Check PDF file integrity
python scripts/utilities/pdf_validator.py input.pdf

# Try alternative extraction method
python scripts/processors/pdf_extractor.py --method pypdf2

# Manual text correction
python scripts/utilities/text_corrector.py input.txt output.txt
```

#### 2. Unicode Encoding Problems

**Symptoms**:
- Corrupted Sinhala/Tamil text
- Question marks in output
- Encoding errors

**Solutions**:
```bash
# Fix encoding issues
python scripts/processors/text_cleaner.py --fix-encoding input.txt

# Convert encoding
iconv -f ISO-8859-1 -t UTF-8 input.txt > output.txt

# Validate character encoding
file -i text_file.txt
```

#### 3. Route Parsing Errors

**Symptoms**:
- Missing routes in output
- Incorrect stop sequences
- Malformed route data

**Solutions**:
```bash
# Debug parsing with verbose output
python scripts/processors/route_parser.py --debug input.txt

# Validate text format
python scripts/utilities/format_validator.py input.txt

# Manual route correction
python scripts/utilities/route_corrector.py input.csv output.csv
```

#### 4. Data Validation Failures

**Symptoms**:
- Schema validation errors
- Business rule violations
- Data inconsistencies

**Solutions**:
```bash
# Run data quality check
python scripts/utilities/data_quality_checker.py

# Fix specific validation errors
python scripts/utilities/data_fixer.py --fix-routes input.json

# Generate validation report
python scripts/utilities/validation_reporter.py --output report.html
```

### Performance Issues

#### Large Dataset Processing

**Problem**: Pipeline times out with large datasets  
**Solutions**:
- Increase timeout in config: `timeout: 600`
- Process in smaller batches: `batch_size: 500`
- Use parallel processing: `max_workers: 8`

#### Memory Usage

**Problem**: Out of memory errors during processing  
**Solutions**:
- Stream processing for large files
- Implement data chunking
- Monitor memory usage with profiler

#### Export Generation Delays

**Problem**: Slow export generation  
**Solutions**:
- Cache intermediate results
- Optimize JSON serialization
- Use compression for large exports

### Data Quality Issues

#### Incomplete Route Information

**Problem**: Missing stops, operators, or fare data  
**Solutions**:
- Cross-reference with official sources
- Implement data completion workflows
- Add manual verification steps

#### Coordinate Accuracy

**Problem**: Inaccurate or missing GPS coordinates  
**Solutions**:
- GPS survey of major routes
- Geocoding service integration
- Crowdsourced coordinate updates

#### Multilingual Support

**Problem**: Missing Sinhala/Tamil translations  
**Solutions**:
- Translation service integration
- Community contribution platform
- Official language authority partnerships

## Maintenance and Updates

### Regular Maintenance Tasks

#### Daily
- Monitor pipeline execution logs
- Check data quality metrics
- Verify export generation

#### Weekly
- Review validation error reports
- Update route information from official sources
- Backup processed data

#### Monthly
- Full data quality audit
- Performance optimization review
- Schema updates if needed

#### Quarterly
- Major data source updates
- Pipeline enhancement deployment
- Comprehensive testing cycle

### Data Update Procedures

#### New PDF Processing
1. Place PDF in `raw-data/sources/ntc-pdf/`
2. Run validation: `python scripts/utilities/pdf_validator.py new.pdf`
3. Execute pipeline: `python scripts/pipelines/full_pipeline.py --pdf new.pdf`
4. Review quality report
5. Deploy to production exports

#### Manual Data Corrections
1. Create correction file in `raw-data/sources/manual-inputs/`
2. Validate format: `python scripts/utilities/format_validator.py corrections.csv`
3. Apply corrections: `python scripts/utilities/data_corrector.py`
4. Re-run validation pipeline
5. Update exports

#### Emergency Updates
1. Identify critical data issue
2. Create hotfix in staging environment
3. Test with sample data
4. Apply to production data
5. Regenerate all exports
6. Notify consuming services

---

**Document Version**: 1.0  
**Last Updated**: December 2025  
**Next Review**: March 2026