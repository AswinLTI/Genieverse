"""
API client module for Blueverse Foundry API interactions.
Handles all API communications with intelligent query routing.
"""

import requests
import logging
from typing import Dict, Any, Optional
from config import API_CONFIG, QUERY_KEYWORDS

logger = logging.getLogger("genieverse.api_client")


class BlueverseAPIClient:
    """Client for Blueverse Foundry API with intelligent routing."""
    
    def __init__(self, api_token: str):
        """
        Initialize the API client.
        
        Args:
            api_token: The API token for authentication
        """
        self.api_token = api_token
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_token}'
        }
        self.base_url = API_CONFIG["base_url"]
        self.timeout = API_CONFIG["timeout"]
    
    def send_query(self, query: str) -> Dict[str, Any]:
        """
        Send query to appropriate API based on content.
        
        Args:
            query: The user query to process
            
        Returns:
            Dict containing the API response
        """
        try:
            api_type = self._classify_query(query)
            
            if api_type == "json_generator":
                return self._send_to_json_generator(query)
            elif api_type == "dashboard":
                return self._create_live_dashboard(query)
            else:
                return self._send_to_main_api(query)
                
        except Exception as e:
            logger.error(f"Error in send_query: {str(e)}")
            return {
                "success": False,
                "error": f"Query processing error: {str(e)}"
            }
    
    def _classify_query(self, query: str) -> str:
        """
        Classify query to determine which API to use.
        
        Args:
            query: The user query to classify
            
        Returns:
            String indicating the API type to use
        """
        query_lower = query.lower()
        
        # Check for dashboard creation indicators
        for keyword in QUERY_KEYWORDS["dashboard"]:
            if keyword in query_lower:
                logger.info(f"Query classified as DASHBOARD based on keyword: {keyword}")
                return "dashboard"
        
        # Check for chart/visualization indicators
        for keyword in QUERY_KEYWORDS["chart"]:
            if keyword in query_lower:
                logger.info(f"Query classified as CHART based on keyword: {keyword}")
                return "json_generator"
        
        # Check for table/data indicators
        for keyword in QUERY_KEYWORDS["table"]:
            if keyword in query_lower:
                logger.info(f"Query classified as TABLE based on keyword: {keyword}")
                return "json_generator"
        
        # Default to main API for simple questions
        logger.info("Query classified as SIMPLE - routing to main API")
        return "main"
    
    def _send_to_main_api(self, query: str) -> Dict[str, Any]:
        """
        Send query to main Blueverse API.
        
        Args:
            query: The user query
            
        Returns:
            Dict containing the API response
        """
        try:
            payload = {
                "query": query,
                "space_name": API_CONFIG["main_api"]["space_name"],
                "flowId": API_CONFIG["main_api"]["flow_id"]
            }
            
            logger.info(f"Sending to MAIN API: {query[:100]}...")
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("Main API request successful")
                return {
                    "success": True,
                    "data": result,
                    "api_used": "main"
                }
            else:
                logger.error(f"Main API request failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"Main API Error {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Main API request exception: {str(e)}")
            return {
                "success": False,
                "error": f"Main API Connection Error: {str(e)}"
            }
    
    def _send_to_json_generator(self, query: str) -> Dict[str, Any]:
        """
        Send query to JSON Generator API for charts and data tables.
        
        Args:
            query: The user query
            
        Returns:
            Dict containing the API response
        """
        try:
            payload = {
                "query": query,
                "space_name": API_CONFIG["json_generator"]["space_name"],
                "flowId": API_CONFIG["json_generator"]["flow_id"]
            }
            
            logger.info(f"Sending to JSON GENERATOR API: {query[:100]}...")
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("JSON Generator API request successful")
                
                # Process the result
                processed_result = self._process_json_generator_response(result)
                
                return {
                    "success": True,
                    "data": processed_result,
                    "api_used": "json_generator"
                }
            else:
                logger.error(f"JSON Generator API request failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"JSON Generator API Error {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"JSON Generator API request exception: {str(e)}")
            return {
                "success": False,
                "error": f"JSON Generator API Connection Error: {str(e)}"
            }
    
    def _process_json_generator_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process JSON Generator response and extract embedded JSON if needed.
        
        Args:
            result: The raw API response
            
        Returns:
            Processed response data
        """
        try:
            # If the result is already a proper chart structure, return as-is
            if isinstance(result, dict) and "status" in result and "chart_type" in result:
                logger.info("Direct chart data format detected")
                return result
            
            # Look for JSON embedded as string in common response fields
            possible_fields = ["response", "message", "content", "data", "result"]
            
            for field in possible_fields:
                if field in result and isinstance(result[field], str):
                    try:
                        import json
                        parsed_json = json.loads(result[field])
                        if isinstance(parsed_json, dict) and "status" in parsed_json:
                            logger.info(f"Found embedded JSON in field: {field}")
                            return parsed_json
                    except json.JSONDecodeError:
                        continue
            
            # If no embedded JSON found, return original result
            logger.info("No embedded JSON found, returning original result")
            return result
            
        except Exception as e:
            logger.error(f"Error processing JSON Generator response: {e}")
            return result
    
    def _create_live_dashboard(self, query: str) -> Dict[str, Any]:
        """
        Create a live dashboard using Streamlit pages system.
        
        Args:
            query: The dashboard creation query
            
        Returns:
            Dict containing the dashboard creation result
        """
        try:
            from dashboard_manager import DashboardManager
            
            logger.info(f"Creating live dashboard for query: {query}")
            
            dashboard_manager = DashboardManager()
            result = dashboard_manager.create_dashboard_from_query(query)
            
            if result["success"]:
                return {
                    "success": True,
                    "data": result["data"],
                    "api_used": "dashboard"
                }
            else:
                return {
                    "success": False,
                    "error": result["error"]
                }
                
        except Exception as e:
            logger.error(f"Dashboard creation error: {str(e)}")
            return {
                "success": False,
                "error": f"Dashboard creation error: {str(e)}"
            }
