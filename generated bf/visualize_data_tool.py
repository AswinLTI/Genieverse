"""
Visualization Tool for Blueverse Foundry Integration
Returns JSON data compatible with Plotly for Streamlit frontend
"""

from langchain_core.tools import tool, BaseTool
import subprocess
import sys

# Function to install missing packages
def install_package(package_name):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
    except Exception as e:
        print(f"Failed to install {package_name}: {str(e)}")

# Import required modules with fallback installation
try:
    import pandas as pd
except ImportError:
    print("Pandas not found. Installing...")
    install_package("pandas")
    import pandas as pd

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    print("Plotly not found. Installing...")
    install_package("plotly")
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

try:
    import logging
except ImportError:
    print("Logging module not found. Installing...")
    install_package("logging")  # Note: `logging` is part of Python's standard library, so this won't be needed.

try:
    import json
except ImportError:
    print("JSON module not found. Installing...")
    install_package("json")  # Note: `json` is part of Python's standard library, so this won't be needed.

from typing import Any, Dict, List, Optional

# Initialize logger
logger = logging.getLogger("visualize_data_tool")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize logger
logger = logging.getLogger("visualize_data")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@tool
def create_chart(
    data: List[Dict],
    chart_type: str,
    x_column: str,
    y_column: str,
    title: Optional[str] = None,
    color_column: Optional[str] = None
) -> dict:
    """Creates visualizations and returns JSON data compatible with Plotly for Streamlit frontend"""
    
    try:
        # Validate input data
        if not data:
            return {"error": "No data provided for visualization"}
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        if df.empty:
            return {"error": "Empty dataset provided"}
        
        # Validate columns exist
        if x_column not in df.columns:
            return {"error": f"Column '{x_column}' not found in data. Available columns: {list(df.columns)}"}
        
        if y_column not in df.columns and chart_type != 'pie':
            return {"error": f"Column '{y_column}' not found in data. Available columns: {list(df.columns)}"}
        
        # Set default title if not provided
        if not title:
            title = f"{chart_type.title()} Chart: {y_column} vs {x_column}"
        
        logger.info(f"Creating {chart_type} chart with {len(df)} data points")
        
        # Create chart based on type
        fig = None
        
        if chart_type == "bar":
            if color_column and color_column in df.columns:
                fig = px.bar(df, x=x_column, y=y_column, color=color_column, title=title)
            else:
                fig = px.bar(df, x=x_column, y=y_column, title=title)
                
        elif chart_type == "line":
            if color_column and color_column in df.columns:
                fig = px.line(df, x=x_column, y=y_column, color=color_column, title=title)
            else:
                fig = px.line(df, x=x_column, y=y_column, title=title)
                
        elif chart_type == "pie":
            # For pie charts, x_column is names, y_column is values
            if y_column in df.columns:
                fig = px.pie(df, names=x_column, values=y_column, title=title)
            else:
                # If no y_column specified, use count of x_column values
                value_counts = df[x_column].value_counts()
                fig = px.pie(values=value_counts.values, names=value_counts.index, title=title)
                
        elif chart_type == "scatter":
            if color_column and color_column in df.columns:
                fig = px.scatter(df, x=x_column, y=y_column, color=color_column, title=title)
            else:
                fig = px.scatter(df, x=x_column, y=y_column, title=title)
                
        elif chart_type == "stacked_bar":
            if not color_column or color_column not in df.columns:
                return {"error": "Stacked bar chart requires a valid color_column for grouping"}
            fig = px.bar(df, x=x_column, y=y_column, color=color_column, title=title)
            
        elif chart_type == "candlestick":
            # Candlestick requires OHLC data
            required_cols = ['Open', 'High', 'Low', 'Close']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                return {"error": f"Candlestick chart requires OHLC data. Missing columns: {missing_cols}"}
            
            # Convert x_column to datetime if it's not already
            if x_column in df.columns:
                df[x_column] = pd.to_datetime(df[x_column])
            
            fig = go.Figure(data=go.Candlestick(
                x=df[x_column],
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name=title or "Candlestick"
            ))
            fig.update_layout(title=title, xaxis_title=x_column, yaxis_title="Price")
            
        else:
            return {"error": f"Unsupported chart type: {chart_type}. Supported types: bar, line, pie, scatter, stacked_bar, candlestick"}
        
        if fig is None:
            return {"error": "Failed to create chart"}
        
        # Convert figure to JSON
        chart_json = fig.to_json()
        
        # Return structured response
        return {
            "result": {
                "chart_json": chart_json,
                "chart_type": chart_type,
                "data_info": {
                    "total_rows": len(df),
                    "columns_used": {
                        "x_column": x_column,
                        "y_column": y_column,
                        "color_column": color_column
                    },
                    "available_columns": list(df.columns)
                },
                "title": title,
                "message": f"Successfully created {chart_type} chart with {len(df)} data points"
            }
        }
        
    except Exception as e:
        logger.error(f"Chart creation failed: {str(e)}")
        return {"error": "Chart creation failed", "details": str(e)}
