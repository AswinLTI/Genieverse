"""
Response processor module for handling API responses and formatting them for display.
Processes different types of API responses and formats them consistently.
"""

import logging
import json
from typing import Dict, Any, Optional
import os

logger = logging.getLogger("genieverse.response_processor")


class ResponseProcessor:
    """Processes API responses and formats them for display."""
    
    def __init__(self):
        """Initialize the response processor."""
        pass
    
    def process_response(self, api_response: Dict[str, Any]) -> str:
        """
        Process API response and extract text content for display.
        
        Args:
            api_response: Raw API response dictionary
            
        Returns:
            Formatted response string for display
        """
        try:
            if not isinstance(api_response, dict):
                return str(api_response)
            
            # Handle different response types
            if self._is_dashboard_response(api_response):
                return self._format_dashboard_response(api_response)
            elif self._is_chart_response(api_response):
                return self._format_chart_response(api_response)
            elif self._is_error_response(api_response):
                return self._format_error_response(api_response)
            else:
                return self._format_general_response(api_response)
                
        except Exception as e:
            logger.error(f"Error processing API response: {e}")
            return f"Error processing response: {str(e)}"
    
    def _is_dashboard_response(self, response: Dict[str, Any]) -> bool:
        """Check if response is a dashboard creation response."""
        return "dashboard_url" in response or "dashboard_path" in response
    
    def _is_chart_response(self, response: Dict[str, Any]) -> bool:
        """Check if response is a chart/data response."""
        return "status" in response and response.get("api_used") == "json_generator"
    
    def _is_error_response(self, response: Dict[str, Any]) -> bool:
        """Check if response indicates an error."""
        return (response.get("success") is False or 
                "error" in response or 
                response.get("status") == "error")
    
    def _format_dashboard_response(self, response: Dict[str, Any]) -> str:
        """Format dashboard creation response."""
        data = response.get("data", response)
        
        # New Streamlit pages format
        if "dashboard_url" in data:
            dashboard_url = data.get("dashboard_url", "")
            title = data.get("title", "Dashboard")
            dashboard_id = data.get("dashboard_id", "")
            page_name = data.get("page_name", "")
            charts = data.get("charts", [])
            
            return f"""✅ **Live dashboard with the requested charts has been created**

🚀 **Dashboard URL:** {dashboard_url}

**Dashboard Details:**
- **Title:** {title}
- **ID:** {dashboard_id}
- **Charts:** {len(charts)} interactive charts
- **Page:** {page_name}

**To access:** The dashboard is now available in your Streamlit app sidebar or visit the URL above."""
        
        # Legacy Python file format
        elif "dashboard_path" in data:
            dashboard_path = data.get("dashboard_path", "")
            title = data.get("title", "Dashboard")
            charts = data.get("charts", [])
            
            file_name = os.path.basename(dashboard_path) if dashboard_path else "dashboard.py"
            dashboard_url = self._get_deployment_url(f"dashboards/{file_name}")
            
            return f"""✅ **Live dashboard with the requested charts has been created**

🔗 **Dashboard Link:** {dashboard_url}

To view: Copy the link above and run the dashboard file using:
`streamlit run "{dashboard_path}"`"""
        
        return "✅ Dashboard created successfully!"
    
    def _format_chart_response(self, response: Dict[str, Any]) -> str:
        """Format chart/data response."""
        data = response.get("data", {})
        
        if data.get("status") == "success":
            chart_type = data.get("chart_type", "")
            data_count = len(data.get("data", []))
            
            if chart_type and data_count > 0:
                return f"✅ Successfully generated {chart_type} chart with {data_count} data points."
            elif data_count > 0:
                return f"✅ Successfully retrieved {data_count} data records."
            else:
                return "✅ Query executed successfully."
        
        elif data.get("status") == "error" or "error" in data:
            error_msg = data.get("error", data.get("message", "Unknown error"))
            return f"❌ {error_msg}"
        
        # Try to extract meaningful content
        return self._extract_response_content(data)
    
    def _format_error_response(self, response: Dict[str, Any]) -> str:
        """Format error response."""
        error_msg = (response.get("error") or 
                    response.get("message") or 
                    response.get("data", {}).get("error") or
                    "Unknown error occurred")
        
        return f"❌ Error: {error_msg}"
    
    def _format_general_response(self, response: Dict[str, Any]) -> str:
        """Format general API response."""
        # Try to find the main response text
        content = self._extract_response_content(response)
        
        if content:
            return content
        
        # If no meaningful content found, return formatted JSON
        return f"Response received:\n```json\n{json.dumps(response, indent=2)}\n```"
    
    def _extract_response_content(self, data: Dict[str, Any]) -> Optional[str]:
        """
        Extract meaningful content from response data.
        
        Args:
            data: Response data dictionary
            
        Returns:
            Extracted content string or None
        """
        # List of fields that commonly contain response text
        possible_fields = [
            "response", "message", "text", "content", "answer", 
            "result", "output", "reply", "description"
        ]
        
        # First, try direct fields
        for field in possible_fields:
            if field in data and isinstance(data[field], str) and data[field].strip():
                return data[field].strip()
        
        # Then try nested data
        if "data" in data and isinstance(data["data"], dict):
            for field in possible_fields:
                if field in data["data"] and isinstance(data["data"][field], str):
                    content = data["data"][field].strip()
                    if content:
                        return content
        
        # Try to extract from embedded JSON strings
        for field in possible_fields:
            if field in data and isinstance(data[field], str):
                try:
                    parsed = json.loads(data[field])
                    if isinstance(parsed, dict):
                        extracted = self._extract_response_content(parsed)
                        if extracted:
                            return extracted
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def format_chart_debug_info(self, chart_data: Dict[str, Any], chart_config: Dict[str, Any]) -> str:
        """
        Format debug information for chart display.
        
        Args:
            chart_data: Chart data from API
            chart_config: Chart configuration
            
        Returns:
            Formatted debug information
        """
        debug_info = []
        
        debug_info.append(f"**Chart Type:** {chart_config.get('type', 'Unknown')}")
        debug_info.append(f"**Chart Title:** {chart_config.get('title', 'Unknown')}")
        debug_info.append(f"**Query:** {chart_config.get('query', 'Unknown')}")
        
        if isinstance(chart_data, dict):
            if "data" in chart_data:
                data = chart_data["data"]
                if isinstance(data, list):
                    debug_info.append(f"**Data Points:** {len(data)}")
                    if data:
                        debug_info.append(f"**Columns:** {list(data[0].keys())}")
            
            debug_info.append(f"**X Column:** {chart_data.get('x', 'Auto-detected')}")
            debug_info.append(f"**Y Column:** {chart_data.get('y', 'Auto-detected')}")
            debug_info.append(f"**Status:** {chart_data.get('status', 'Unknown')}")
        
        return "\n".join(debug_info)
    
    def extract_error_details(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract detailed error information from response.
        
        Args:
            response: API response
            
        Returns:
            Dict containing error details
        """
        error_details = {
            "has_error": False,
            "error_message": "",
            "error_type": "",
            "status_code": None,
            "api_used": response.get("api_used", "unknown")
        }
        
        if response.get("success") is False:
            error_details["has_error"] = True
            error_details["error_message"] = response.get("error", "Unknown error")
            error_details["error_type"] = "api_error"
        
        elif "error" in response:
            error_details["has_error"] = True
            error_details["error_message"] = response["error"]
            error_details["error_type"] = "response_error"
        
        elif isinstance(response.get("data"), dict) and response["data"].get("status") == "error":
            error_details["has_error"] = True
            error_details["error_message"] = response["data"].get("message", "Unknown error")
            error_details["error_type"] = "data_error"
        
        return error_details
    
    def _get_deployment_url(self, page_path: str) -> str:
        """
        Generate deployment-ready URL for dashboard pages.
        
        Args:
            page_path: Path to the page
            
        Returns:
            str: Deployment-ready URL
        """
        try:
            # Import here to avoid circular imports
            from config import get_deployment_base_url
            
            base_url = get_deployment_base_url()
            
            if base_url:
                return f"{base_url}/{page_path}"
            else:
                # For Streamlit Cloud, use relative URLs
                return f"/{page_path}"
            
        except Exception:
            # Fallback to relative URL for deployment compatibility
            return f"/{page_path}"
