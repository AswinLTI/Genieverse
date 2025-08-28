"""
Configuration module for Genieverse application.
Contains all configuration constants and settings.
"""

import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Application Configuration
APP_CONFIG = {
    "title": "Genieverse",
    "layout": "wide",
    "page_icon": "🧞",
    "initial_sidebar_state": "expanded"
}

# API Configuration
API_CONFIG = {
    "base_url": "https://blueverse-foundry.ltimindtree.com/chatservice/chat",
    "timeout": 60,
    "main_api": {
        "space_name": "Genieverse_9b5befb3",
        "flow_id": "68ac66333c336dbd12b96e10"
    },
    "json_generator": {
        "space_name": "Json_Generator_975a2dc0",
        "flow_id": "68ae94113d219c7a19e1446d"
    }
}

# Query Classification Keywords
QUERY_KEYWORDS = {
    "dashboard": [
        "dashboard", "live dashboard", "create dashboard", "build dashboard",
        "dashboard with", "interactive dashboard", "real-time dashboard"
    ],
    "chart": [
        "chart", "plot", "graph", "visualize", "visualization", "bar chart", "line chart",
        "pie chart", "scatter plot", "histogram", "heatmap", "candlestick", "stacked bar",
        "create chart", "show chart", "generate chart", "plot data", "visualize data"
    ],
    "table": [
        "table", "raw data", "show data", "view data", "display data", "data table",
        "show table", "preview data", "sample data", "first rows", "head", "limit",
        "select", "query", "sql", "dataframe", "dataset"
    ]
}

# Chart Configuration
CHART_CONFIG = {
    "dark_theme": {
        "background_color": "rgba(0,0,0,0)",
        "text_color": "#ffffff",
        "grid_color": "rgba(255,255,255,0.2)",
        "font_family": "Arial, sans-serif"
    },
    "colors": [
        "#4FC3F7", "#81C784", "#FFB74D", "#F06292", "#BA68C8", 
        "#64B5F6", "#4DB6AC", "#A1C181", "#FF8A65", "#9575CD"
    ],
    "supported_types": ["bar", "pie", "line", "scatter", "candlestick"]
}

# File Paths
PATHS = {
    "dashboards_dir": "dashboards",
    "pages_dir": "pages",
    "registry_file": os.path.join("dashboards", "dashboard_registry.json"),
    "static_dir": "../static",
    "genie_image": "../static/genie.png"
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    "max_charts_per_row": 2,
    "default_chart_height": 400,
    "auto_refresh_interval": 300,  # 5 minutes in seconds
    "max_data_points": 1000
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "logger_name": "genieverse"
}

def get_api_token() -> str:
    """Get API token from environment variables."""
    return os.getenv("BLUEVERSE_API_TOKEN", "")

def get_base_url() -> str:
    """Get the base URL for the current environment."""
    return API_CONFIG["base_url"]

def validate_config() -> bool:
    """Validate that all required configuration is present."""
    required_paths = [PATHS["static_dir"]]
    
    for path in required_paths:
        if not os.path.exists(path):
            print(f"Warning: Required path not found: {path}")
            return False
    
    return True
