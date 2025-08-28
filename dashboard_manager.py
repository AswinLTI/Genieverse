"""
Dashboard management module for creating and managing Streamlit dashboard pages.
Handles dashboard creation, registry management, and page generation.
"""

import os
import json
import datetime
import re
import logging
from typing import Dict, Any, List, Optional
from config import PATHS, DASHBOARD_CONFIG
from utils import create_streamlit_page, generate_dashboard_page_content, add_to_dashboard_registry, clean_filename

logger = logging.getLogger("genieverse.dashboard_manager")


class DashboardManager:
    """Manages dashboard creation, storage, and retrieval."""
    
    def __init__(self):
        """Initialize the dashboard manager."""
        self.registry_file = PATHS["registry_file"]
        self.pages_dir = PATHS["pages_dir"]
        self.dashboards_dir = PATHS["dashboards_dir"]
        
        # Ensure required directories exist
        os.makedirs(self.pages_dir, exist_ok=True)
        os.makedirs(self.dashboards_dir, exist_ok=True)
    
    def create_dashboard_from_query(self, query: str) -> Dict[str, Any]:
        """
        Create a dashboard from a natural language query.
        
        Args:
            query: The dashboard creation query
            
        Returns:
            Dict containing the creation result
        """
        try:
            # Parse the dashboard requirements from the query
            dashboard_config = self._parse_dashboard_query(query)
            
            if not dashboard_config:
                return {
                    "success": False,
                    "error": "Could not parse dashboard requirements from query"
                }
            
            # Generate the dashboard page
            dashboard_info = self._generate_dashboard_page(dashboard_config, query)
            
            if dashboard_info:
                return {
                    "success": True,
                    "data": {
                        "dashboard_url": dashboard_info["url"],
                        "dashboard_id": dashboard_info["dashboard_id"],
                        "page_name": dashboard_info["page_name"],
                        "dashboard_config": dashboard_config,
                        "charts": dashboard_config["charts"],
                        "title": dashboard_config["title"]
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create dashboard page"
                }
                
        except Exception as e:
            logger.error(f"Dashboard creation error: {str(e)}")
            return {
                "success": False,
                "error": f"Dashboard creation error: {str(e)}"
            }
    
    def _parse_dashboard_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Parse dashboard requirements from natural language query.
        
        Args:
            query: The natural language query
            
        Returns:
            Dict containing dashboard configuration or None
        """
        charts = []
        query_lower = query.lower()
        
        # Split on common separators to handle multiple chart requests
        sentences = re.split(r'[.!?]\s*(?:and\s+)?|(?:\s+and\s+)', query_lower)
        
        # Define improved chart patterns for each sentence
        chart_patterns = {
            "bar": [
                r'bar chart.+?(?:for|of|showing|with)\s+(.+?)(?:\s*$)',
                r'bar chart.+?(.+?)(?:\s*$)',
                r'(?:create|make|generate|build)\s+(?:a\s+)?bar chart.+?(?:for|of|showing|with)\s+(.+?)(?:\s*$)',
                r'top\s+\d*\s*customers?\s+by\s+spend',
                r'customers?\s+by\s+(?:total\s+)?spend'
            ],
            "pie": [
                r'pie chart.+?(?:for|of|showing|with)\s+(.+?)(?:\s*$)',
                r'pie chart.+?(.+?)(?:\s*$)',
                r'(?:create|make|generate|build)\s+(?:a\s+)?pie chart.+?(?:for|of|showing|with)\s+(.+?)(?:\s*$)',
                r'product\s+categories?(?:\s+pie\s+chart)?',
                r'categories?\s+(?:pie\s+chart|distribution)'
            ],
            "line": [
                r'line chart.+?(?:for|of|showing|with)\s+(.+?)(?:\s*$)',
                r'line chart.+?(.+?)(?:\s*$)',
                r'(?:create|make|generate|build)\s+(?:a\s+)?line chart.+?(?:for|of|showing|with)\s+(.+?)(?:\s*$)'
            ]
        }
        
        # Process each sentence/segment
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 5:
                continue
                
            # Check for each chart type in this sentence
            for chart_type, patterns in chart_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, sentence):
                        # Extract description
                        match = re.search(pattern, sentence)
                        if match and match.groups():
                            description = match.group(1).strip()
                        else:
                            # Use predefined descriptions for common patterns
                            if chart_type == "bar" and ("customer" in sentence and "spend" in sentence):
                                description = "top 10 customers by spend"
                            elif chart_type == "pie" and ("product" in sentence and "categor" in sentence):
                                description = "product categories"
                            else:
                                description = sentence.replace("chart", "").replace(chart_type, "").strip()
                        
                        # Clean up description
                        description = re.sub(r'^(for|of|showing|with)\s+', '', description)
                        description = description.strip()
                        
                        if description:
                            chart_title = f"{chart_type.title()} Chart: {description.title()}"
                            chart_query = f"Create a {chart_type} chart for {description}"
                            
                            # Avoid duplicates
                            if not any(c["description"] == description and c["type"] == chart_type for c in charts):
                                charts.append({
                                    "type": chart_type,
                                    "title": chart_title,
                                    "description": description,
                                    "query": chart_query
                                })
                        break  # Found a match for this chart type in this sentence
        
        # Enhanced fallback: create specific charts based on common keywords
        if not charts:
            if 'customer' in query_lower and 'spend' in query_lower:
                charts.append({
                    "type": "bar",
                    "title": "Bar Chart: Top Customers By Spend",
                    "description": "top 10 customers by spend",
                    "query": "Create a bar chart for top 10 customers by spend"
                })
            
            if ('categories' in query_lower or 'category' in query_lower) and 'product' in query_lower:
                charts.append({
                    "type": "pie",
                    "title": "Pie Chart: Product Categories",
                    "description": "product categories",
                    "query": "Create a pie chart for product categories"
                })
        
        if charts:
            return {
                "title": "Live Dashboard",
                "charts": charts
            }
        
        return None
    
    def _generate_dashboard_page(self, config: Dict[str, Any], original_query: str) -> Optional[Dict[str, Any]]:
        """
        Generate a Streamlit page for the dashboard using the pages system.
        
        Args:
            config: Dashboard configuration
            original_query: The original query that triggered creation
            
        Returns:
            Dict containing page information or None
        """
        try:
            # Create unique dashboard ID
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create clean page name
            title_clean = clean_filename(config['title'])
            page_name = f"dashboard_{title_clean}_{timestamp}"
            dashboard_id = f"dash_{timestamp}"
            
            # Generate page content
            page_content = generate_dashboard_page_content(config, dashboard_id)
            
            # Create the page file
            page_path = create_streamlit_page(page_name, page_content)
            
            # Add to registry
            dashboard_entry = add_to_dashboard_registry(config, page_path, dashboard_id)
            
            if dashboard_entry:
                logger.info(f"Dashboard page created: {page_path}")
                return {
                    "url": dashboard_entry["url"],
                    "dashboard_id": dashboard_id,
                    "page_name": page_name,
                    "page_path": page_path
                }
            else:
                logger.error("Failed to add dashboard to registry")
                return None
            
        except Exception as e:
            logger.error(f"Error generating dashboard page: {e}")
            return None
    
    def get_dashboard_registry(self) -> List[Dict[str, Any]]:
        """
        Get the current dashboard registry.
        
        Returns:
            List of dashboard entries
        """
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading dashboard registry: {e}")
                return []
        return []
    
    def remove_dashboard(self, index: int) -> bool:
        """
        Remove a dashboard from the registry.
        
        Args:
            index: Index of the dashboard to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            registry = self.get_dashboard_registry()
            if 0 <= index < len(registry):
                # Remove the dashboard entry
                removed_dashboard = registry.pop(index)
                
                # Save updated registry
                with open(self.registry_file, 'w') as f:
                    json.dump(registry, f, indent=2)
                
                # Optionally remove the page file
                if "page_path" in removed_dashboard:
                    page_path = removed_dashboard["page_path"]
                    if os.path.exists(page_path):
                        try:
                            os.remove(page_path)
                            logger.info(f"Removed page file: {page_path}")
                        except Exception as e:
                            logger.warning(f"Could not remove page file {page_path}: {e}")
                
                logger.info(f"Removed dashboard: {removed_dashboard.get('title', 'Unknown')}")
                return True
            else:
                logger.error(f"Invalid dashboard index: {index}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing dashboard: {e}")
            return False
    
    def clear_registry(self) -> bool:
        """
        Clear the entire dashboard registry.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(self.registry_file):
                os.remove(self.registry_file)
                logger.info("Dashboard registry cleared")
                return True
            return True
            
        except Exception as e:
            logger.error(f"Error clearing registry: {e}")
            return False
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the dashboard registry.
        
        Returns:
            Dict containing registry statistics
        """
        registry = self.get_dashboard_registry()
        
        total_dashboards = len(registry)
        total_charts = sum(len(dashboard.get("charts", [])) for dashboard in registry)
        
        # Count by type
        chart_types = {}
        for dashboard in registry:
            for chart in dashboard.get("charts", []):
                chart_type = chart.get("type", "unknown")
                chart_types[chart_type] = chart_types.get(chart_type, 0) + 1
        
        # Find newest and oldest
        newest = None
        oldest = None
        if registry:
            sorted_registry = sorted(registry, key=lambda x: x.get("created", ""))
            oldest = sorted_registry[0] if sorted_registry else None
            newest = sorted_registry[-1] if sorted_registry else None
        
        return {
            "total_dashboards": total_dashboards,
            "total_charts": total_charts,
            "chart_types": chart_types,
            "newest_dashboard": newest,
            "oldest_dashboard": oldest
        }
