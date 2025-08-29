"""
Robust JSON Response Parser for Handling Truncated API Responses
This module provides intelligent parsing for incomplete JSON responses from APIs.
"""

import json
import re
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger("genieverse.json_parser")


class RobustJSONParser:
    """
    A robust JSON parser that can handle truncated, malformed, or incomplete JSON responses.
    Specifically designed for chart data extraction from API responses.
    """
    
    def __init__(self):
        """Initialize the parser with common patterns."""
        self.chart_patterns = {
            'status_success': r'"status"\s*:\s*"success"',
            'chart_type': r'"chart_type"\s*:\s*"([^"]+)"',
            'data_array_start': r'"data"\s*:\s*\[',
            'record_pattern': r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
            'date_field': r'"Date"\s*:\s*"([^"]+)"',
            'numeric_field': r'"(\w+)"\s*:\s*(\d+(?:\.\d+)?)',
        }
        
        self.supported_chart_types = ['candlestick', 'scatter', 'line', 'bar', 'pie']
        
    def _clean_truncated_response(self, response_text: str) -> str:
        """
        Clean and repair truncated JSON response by removing incomplete data.
        
        Args:
            response_text: Raw response text that may be truncated
            
        Returns:
            Cleaned response text with incomplete parts removed
        """
        cleaned_text = response_text.strip()
        
        # Find the last complete data record
        data_start = cleaned_text.find('"data": [')
        if data_start == -1:
            return cleaned_text
        
        # Find all complete record patterns
        records_section = cleaned_text[data_start:]
        complete_records = []
        
        # Extract complete records one by one
        record_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.finditer(record_pattern, records_section)
        
        for match in matches:
            record_text = match.group()
            try:
                # Test if this record can be parsed as valid JSON
                json.loads(record_text)
                complete_records.append(record_text)
            except json.JSONDecodeError:
                # Skip incomplete records
                logger.debug(f"Skipping incomplete record: {record_text[:50]}...")
                continue
        
        if complete_records:
            # Reconstruct the response with only complete records
            before_data = cleaned_text[:data_start]
            records_json = ', '.join(complete_records)
            
            # Try to find any metadata after the data array
            after_data_pattern = r'\]\s*,\s*("[\w":\s,]+)\s*\}?\s*$'
            after_data_match = re.search(after_data_pattern, cleaned_text)
            after_data = ""
            
            if after_data_match:
                after_data = ", " + after_data_match.group(1)
            
            # Reconstruct complete JSON
            reconstructed = f'{before_data}"data": [{records_json}]{after_data}}}'
            
            logger.info(f"Cleaned response: removed incomplete data, kept {len(complete_records)} complete records")
            return reconstructed
        
        return cleaned_text

    def _is_error_response(self, response_text: str) -> bool:
        """Check if the response contains an error message."""
        error_indicators = [
            '"error":', 'TABLE_OR_VIEW_NOT_FOUND', 'SQLSTATE', 
            'error', 'ERROR', 'Exception', 'Failed', 'cannot be found'
        ]
        return any(indicator in response_text for indicator in error_indicators)
    
    def _extract_error_message(self, response_text: str) -> Dict[str, Any]:
        """Extract clean error message from error response."""
        try:
            # Try to parse as JSON first
            if response_text.strip().startswith('{'):
                try:
                    parsed = json.loads(response_text)
                    if isinstance(parsed, dict) and 'error' in parsed:
                        error_msg = parsed['error']
                        # Extract clean message from complex error strings
                        clean_msg = self._clean_error_message(error_msg)
                        return {
                            'status': 'error',
                            'error': clean_msg,
                            'error_type': 'database',
                            'chart_data': None
                        }
                except json.JSONDecodeError:
                    pass
            
            # Extract error from text patterns
            clean_msg = self._clean_error_message(response_text)
            return {
                'status': 'error',
                'error': clean_msg,
                'error_type': 'general',
                'chart_data': None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': 'Failed to parse error response',
                'error_type': 'parser',
                'chart_data': None
            }
    
    def _clean_error_message(self, error_text: str) -> str:
        """Extract clean, user-friendly error message."""
        # Common error patterns and their clean versions
        if 'TABLE_OR_VIEW_NOT_FOUND' in error_text:
            if 'TCS_stock' in error_text:
                return "TCS stock data not found in database. Please check if the data exists for the requested time period."
            else:
                return "Requested stock data table not found in database."
        
        if 'SQLSTATE' in error_text:
            # Extract the main error message before SQLSTATE
            parts = error_text.split('SQLSTATE')
            if parts:
                main_error = parts[0].strip()
                # Remove technical prefixes
                main_error = main_error.replace('[TABLE_OR_VIEW_NOT_FOUND]', '').strip()
                if main_error:
                    return main_error
        
        # For other errors, try to extract meaningful message
        if 'cannot be found' in error_text:
            return "The requested data source cannot be found. Please verify the stock symbol and date range."
        
        if 'Failed to' in error_text or 'Error:' in error_text:
            return error_text.split('\n')[0]  # Return first line of error
        
        # Default cleanup
        clean_msg = error_text.strip()
        if len(clean_msg) > 200:
            clean_msg = clean_msg[:200] + "..."
        
        return clean_msg or "An error occurred while processing the request."

    def parse_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a potentially truncated JSON response and extract chart data.
        Automatically cleans incomplete data to ensure valid JSON is always returned.
        Also handles error responses and extracts clean error messages.
        
        Args:
            response_text: Raw response text that may contain incomplete JSON or errors
            
        Returns:
            Parsed chart data dictionary or error information
        """
        try:
            # First check if this is an error response
            if self._is_error_response(response_text):
                return self._extract_error_message(response_text)
            
            # Clean the response first to remove incomplete data
            cleaned_response = self._clean_truncated_response(response_text)
            
            # First, try normal JSON parsing on cleaned response
            if cleaned_response.strip().startswith('{'):
                try:
                    parsed_json = json.loads(cleaned_response)
                    if isinstance(parsed_json, dict) and parsed_json.get('status') == 'success':
                        logger.info("Successfully parsed cleaned JSON response")
                        return self._enhance_chart_data(parsed_json)
                except json.JSONDecodeError:
                    logger.info("Standard JSON parsing failed even after cleaning, attempting pattern extraction")
            
            # If standard parsing fails, use pattern-based extraction
            chart_info = self._extract_chart_metadata(response_text)
            if not chart_info:
                logger.warning("Could not extract chart metadata from response")
                return None
            
            # Extract data records
            data_records = self._extract_data_records(response_text, chart_info['chart_type'])
            if not data_records:
                logger.warning("Could not extract data records from response")
                return None
            
            # Construct the complete chart data
            result = {
                "status": "success",
                "chart_type": chart_info['chart_type'],
                "data": data_records,
                "x": chart_info.get('x_column', self._detect_x_column(data_records)),
                "y": chart_info.get('y_columns', self._detect_y_columns(data_records, chart_info['chart_type']))
            }
            
            logger.info(f"Successfully parsed {len(data_records)} records for {chart_info['chart_type']} chart")
            return result
            
        except Exception as e:
            logger.error(f"Error in robust JSON parsing: {e}")
            return None
    
    def _enhance_chart_data(self, chart_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance chart data to ensure it has all required fields for rendering.
        
        Args:
            chart_data: Parsed chart data dictionary
            
        Returns:
            Enhanced chart data with all required fields
        """
        enhanced_data = chart_data.copy()
        
        # Ensure status is set
        if 'status' not in enhanced_data:
            enhanced_data['status'] = 'success'
        
        # Auto-detect chart type if missing
        if 'chart_type' not in enhanced_data and 'data' in enhanced_data:
            enhanced_data['chart_type'] = self._detect_chart_type_from_data(enhanced_data['data'])
        
        # Auto-detect and set x/y columns if missing
        if 'data' in enhanced_data and enhanced_data['data']:
            if 'x' not in enhanced_data:
                enhanced_data['x'] = self._detect_x_column(enhanced_data['data'])
            if 'y' not in enhanced_data:
                enhanced_data['y'] = self._detect_y_columns(
                    enhanced_data['data'], 
                    enhanced_data.get('chart_type', 'line')
                )
        
        # Add metadata about data completeness
        if 'data' in enhanced_data:
            enhanced_data['data_count'] = len(enhanced_data['data'])
            enhanced_data['data_complete'] = True  # Since we cleaned incomplete records
        
        # Add parser metadata
        enhanced_data['parser_info'] = {
            'method': 'robust_parser_v2',
            'version': '2.0',
            'features': ['truncation_handling', 'auto_detection', 'data_cleaning']
        }
        
        logger.info(f"Enhanced chart data with {enhanced_data.get('data_count', 0)} complete records")
        return enhanced_data
    
    def _detect_chart_type_from_data(self, data_records: List[Dict[str, Any]]) -> str:
        """Detect chart type from data structure."""
        if not data_records:
            return 'line'
        
        first_record = data_records[0]
        columns = list(first_record.keys())
        
        # Candlestick: has OHLC columns
        if all(col in columns for col in ['Open', 'High', 'Low', 'Close']):
            return 'candlestick'
        
        # Scatter: has two numeric columns (usually Open/Close)
        numeric_cols = [col for col in columns if isinstance(first_record.get(col), (int, float))]
        if len(numeric_cols) >= 2:
            return 'scatter'
        
        # Default to line chart
        return 'line'
    
    def _extract_chart_metadata(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract chart metadata from response text."""
        metadata = {}
        
        # Check for success status
        if not re.search(self.chart_patterns['status_success'], text):
            return None
        
        # Extract chart type
        chart_type_match = re.search(self.chart_patterns['chart_type'], text)
        if not chart_type_match:
            return None
            
        chart_type = chart_type_match.group(1)
        if chart_type not in self.supported_chart_types:
            logger.warning(f"Unsupported chart type: {chart_type}")
            return None
        
        metadata['chart_type'] = chart_type
        return metadata
    
    def _extract_data_records(self, text: str, chart_type: str) -> List[Dict[str, Any]]:
        """Extract data records from the response text."""
        # Find the data array start
        data_start_match = re.search(self.chart_patterns['data_array_start'], text)
        if not data_start_match:
            return []
        
        # Extract all record-like structures after the data array start
        data_section = text[data_start_match.end():]
        record_matches = re.findall(self.chart_patterns['record_pattern'], data_section)
        
        parsed_records = []
        for record_text in record_matches:
            try:
                # Try to parse each record as JSON
                record = json.loads(record_text)
                
                # Validate the record has required fields for the chart type
                if self._validate_record(record, chart_type):
                    parsed_records.append(record)
                    
            except json.JSONDecodeError:
                # If JSON parsing fails, try manual field extraction
                record = self._extract_fields_manually(record_text)
                if record and self._validate_record(record, chart_type):
                    parsed_records.append(record)
        
        return parsed_records
    
    def _extract_fields_manually(self, record_text: str) -> Optional[Dict[str, Any]]:
        """Manually extract fields from a record string when JSON parsing fails."""
        record = {}
        
        try:
            # Extract date field
            date_match = re.search(self.chart_patterns['date_field'], record_text)
            if date_match:
                record['Date'] = date_match.group(1)
            
            # Extract numeric fields
            numeric_matches = re.findall(self.chart_patterns['numeric_field'], record_text)
            for field_name, field_value in numeric_matches:
                if field_name != 'Date':  # Skip date field
                    try:
                        record[field_name] = float(field_value)
                    except ValueError:
                        continue
            
            return record if len(record) > 1 else None  # Need at least 2 fields
            
        except Exception as e:
            logger.error(f"Manual field extraction failed: {e}")
            return None
    
    def _validate_record(self, record: Dict[str, Any], chart_type: str) -> bool:
        """Validate that a record has the required fields for the chart type."""
        if not isinstance(record, dict):
            return False
        
        required_fields = self._get_required_fields(chart_type)
        return all(field in record for field in required_fields)
    
    def _get_required_fields(self, chart_type: str) -> List[str]:
        """Get required fields for a specific chart type."""
        field_requirements = {
            'candlestick': ['Date', 'Open', 'High', 'Low', 'Close'],
            'scatter': ['Date'],  # Plus any two numeric fields
            'line': ['Date'],     # Plus at least one numeric field
            'bar': [],            # At least two fields
            'pie': []             # At least two fields
        }
        
        return field_requirements.get(chart_type, ['Date'])
    
    def _detect_x_column(self, records: List[Dict[str, Any]]) -> str:
        """Auto-detect the X column from data records."""
        if not records:
            return "Date"
        
        # Look for common X-axis field names
        sample_record = records[0]
        x_candidates = ['Date', 'date', 'time', 'Time', 'timestamp', 'Timestamp']
        
        for candidate in x_candidates:
            if candidate in sample_record:
                return candidate
        
        # If no date field found, use the first field
        return list(sample_record.keys())[0] if sample_record else "Date"
    
    def _detect_y_columns(self, records: List[Dict[str, Any]], chart_type: str) -> List[str]:
        """Auto-detect Y columns based on chart type and data."""
        if not records:
            return []
        
        sample_record = records[0]
        numeric_fields = [k for k, v in sample_record.items() 
                         if isinstance(v, (int, float)) and k not in ['Date', 'date']]
        
        if chart_type == 'candlestick':
            return ['Open', 'High', 'Low', 'Close']
        elif chart_type == 'scatter':
            # For scatter plots, return first two numeric fields
            return numeric_fields[:2] if len(numeric_fields) >= 2 else numeric_fields
        elif chart_type in ['line', 'bar']:
            # For line/bar charts, return first numeric field
            return numeric_fields[:1] if numeric_fields else []
        else:
            return numeric_fields
    
    def get_parsing_stats(self, original_response: str, parsed_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get statistics about the parsing operation."""
        stats = {
            "original_length": len(original_response),
            "parsing_successful": parsed_data is not None,
            "records_extracted": len(parsed_data.get("data", [])) if parsed_data else 0,
            "chart_type": parsed_data.get("chart_type", "unknown") if parsed_data else "unknown",
            "truncated_response": not original_response.strip().endswith('}')
        }
        
        if parsed_data:
            stats["data_columns"] = list(parsed_data["data"][0].keys()) if parsed_data["data"] else []
            stats["x_column"] = parsed_data.get("x", "unknown")
            stats["y_columns"] = parsed_data.get("y", [])
        
        return stats


def enhance_main_app_with_robust_parsing():
    """
    This function shows how to integrate the robust parser into the main app.
    This should replace the current extract_chart_data function.
    """
    def extract_chart_data_robust(api_response):
        """Enhanced chart data extraction with robust JSON parsing."""
        try:
            # First, try the existing logic for properly formatted responses
            if isinstance(api_response, dict):
                if "status" in api_response and api_response.get("status") == "success":
                    if "data" in api_response and api_response["data"]:
                        return {"json_generator_data": api_response}
            
            # If that fails, use robust parsing
            parser = RobustJSONParser()
            
            # Try to extract response text from various fields
            response_text = None
            if isinstance(api_response, str):
                response_text = api_response
            elif isinstance(api_response, dict):
                for field in ["response", "message", "content", "data", "result"]:
                    if field in api_response and isinstance(api_response[field], str):
                        response_text = api_response[field]
                        break
            
            if not response_text:
                logger.warning("No text content found for robust parsing")
                return None
            
            # Parse the response
            parsed_data = parser.parse_response(response_text)
            
            if parsed_data:
                # Get parsing statistics for debugging
                stats = parser.get_parsing_stats(response_text, parsed_data)
                logger.info(f"Robust parsing stats: {stats}")
                
                return {"json_generator_data": parsed_data}
            
            return None
            
        except Exception as e:
            logger.error(f"Error in robust chart data extraction: {e}")
            return None
    
    return extract_chart_data_robust


# Example usage and testing
if __name__ == "__main__":
    # Test with truncated Wipro scatter plot response
    truncated_response = '''{ "status": "success", "chart_type": "scatter", "data": [ { "Open": 551.0, "Close": 545.45, "Date": "2016-05-31" }, { "Open": 547.2, "Close": 550.15, "Date": "2016-05-30" }, { "Open": 543.15, "Close": 545.4, "Date": "2016-05-27" }'''
    
    parser = RobustJSONParser()
    result = parser.parse_response(truncated_response)
    
    if result:
        print("✅ Robust parsing successful!")
        print(f"Chart type: {result['chart_type']}")
        print(f"Records extracted: {len(result['data'])}")
        print(f"X column: {result['x']}")
        print(f"Y columns: {result['y']}")
    else:
        print("❌ Robust parsing failed")
