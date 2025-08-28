"""
Chart utilities module for creating and managing Plotly charts.
Handles chart creation, styling, and data processing.
"""

import pandas as pd
import plotly.graph_objects as go
import json
import logging
from typing import Dict, Any, Optional, List
from config import CHART_CONFIG

logger = logging.getLogger("genieverse.chart_utils")


class ChartBuilder:
    """Builder class for creating Plotly charts with consistent styling."""
    
    def __init__(self):
        """Initialize the chart builder with default configuration."""
        self.colors = CHART_CONFIG["colors"]
        self.dark_theme = CHART_CONFIG["dark_theme"]
        self.supported_types = CHART_CONFIG["supported_types"]
    
    def create_chart(self, chart_data: Dict[str, Any], chart_type: str, title: str = "") -> Optional[go.Figure]:
        """
        Create a Plotly chart with dark theme styling.
        
        Args:
            chart_data: Data for the chart
            chart_type: Type of chart (bar, pie, line, scatter)
            title: Chart title
            
        Returns:
            Plotly Figure object or None if creation fails
        """
        try:
            # Normalize chart type to handle variations
            chart_type = chart_type.lower().strip()
            if "scatter" in chart_type:
                chart_type = "scatter"
            elif "bar" in chart_type:
                chart_type = "bar"
            elif "pie" in chart_type:
                chart_type = "pie"
            elif "line" in chart_type:
                chart_type = "line"
            elif "candlestick" in chart_type:
                chart_type = "candlestick"
            
            if chart_type not in self.supported_types:
                logger.error(f"Unsupported chart type: {chart_type}")
                return None
            
            # Extract and validate data
            processed_data = self._process_chart_data(chart_data)
            if not processed_data:
                logger.error("No valid data found for chart creation")
                return None
            
            # Generate intelligent title if not provided
            if not title:
                title = self._generate_chart_title(processed_data, chart_type)
            
            # Create chart based on type
            if chart_type == "bar":
                return self._create_bar_chart(processed_data, title)
            elif chart_type == "pie":
                return self._create_pie_chart(processed_data, title)
            elif chart_type == "line":
                return self._create_line_chart(processed_data, title)
            elif chart_type == "scatter":
                return self._create_scatter_chart(processed_data, title)
            elif chart_type == "candlestick":
                return self._create_candlestick_chart(processed_data, title)
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating {chart_type} chart: {e}")
            return None
    
    def _generate_chart_title(self, processed_data: Dict[str, Any], chart_type: str) -> str:
        """
        Generate an intelligent title for the chart based on data and chart type.
        
        Args:
            processed_data: Processed chart data
            chart_type: Type of chart
            
        Returns:
            Generated title string
        """
        try:
            x_col = processed_data.get("x_col", "X")
            y_col = processed_data.get("y_col", "Y")
            data = processed_data.get("data", [])
            
            # Format column names for better display
            x_display = self._format_column_name(x_col)
            y_display = self._format_column_name(y_col)
            
            # Generate title based on chart type
            if chart_type == "bar":
                return f"{y_display} by {x_display}"
            elif chart_type == "pie":
                return f"Distribution of {y_display}"
            elif chart_type == "line":
                return f"{y_display} over {x_display}"
            elif chart_type == "scatter":
                return f"{y_display} vs {x_display}"
            elif chart_type == "candlestick":
                return f"OHLC Price Chart"
            else:
                return f"{y_display} by {x_display}"
                
        except Exception as e:
            logger.error(f"Error generating chart title: {e}")
            return "Chart"
    
    def _format_column_name(self, col_name: str) -> str:
        """
        Format column name for better display in titles.
        
        Args:
            col_name: Raw column name
            
        Returns:
            Formatted column name
        """
        if not col_name:
            return "Value"
        
        # Replace underscores with spaces and title case
        formatted = col_name.replace("_", " ").replace("-", " ")
        
        # Handle common abbreviations and patterns
        formatted = formatted.replace("id", "ID")
        formatted = formatted.replace("Id", "ID")
        formatted = formatted.replace("url", "URL")
        formatted = formatted.replace("api", "API")
        formatted = formatted.replace("sql", "SQL")
        
        # Title case each word
        return " ".join(word.capitalize() for word in formatted.split())
    
    def _process_chart_data(self, chart_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process and validate chart data from API response.
        
        Args:
            chart_data: Raw chart data from API
            
        Returns:
            Processed data dict or None
        """
        try:
            # Extract data from various response formats
            data = None
            x_col = ""
            y_col = ""
            
            logger.info(f"Processing chart data with keys: {list(chart_data.keys()) if isinstance(chart_data, dict) else 'not dict'}")
            
            if isinstance(chart_data, dict):
                if "data" in chart_data and chart_data["data"]:
                    data = chart_data["data"]
                    x_col = chart_data.get("x", "")
                    y_col = chart_data.get("y", "")
                    logger.info(f"Found data with {len(data)} items, x_col: {x_col}, y_col: {y_col}")
                elif "response" in chart_data:
                    try:
                        parsed = json.loads(chart_data["response"])
                        if "data" in parsed:
                            data = parsed["data"]
                            x_col = parsed.get("x", "")
                            y_col = parsed.get("y", "")
                    except json.JSONDecodeError:
                        logger.warning("Could not parse JSON from response field")
            
            if not data:
                logger.error("No data found in chart_data")
                return None
            
            # Ensure data is a list
            if not isinstance(data, list):
                logger.error(f"Data is not a list, it's {type(data)}")
                return None
                
            if not data:
                logger.error("Data list is empty")
                return None
            
            # Auto-detect columns if not specified
            if isinstance(data, list) and data:
                columns = list(data[0].keys()) if data[0] and isinstance(data[0], dict) else []
                logger.info(f"Available columns: {columns}")
                
                # Special handling for candlestick charts
                if isinstance(y_col, list) and len(y_col) >= 4:
                    # This is likely a candlestick chart with [Open, High, Low, Close]
                    logger.info("Detected candlestick chart format with OHLC columns")
                    candlestick_cols = ['Open', 'High', 'Low', 'Close']
                    
                    # Verify all required columns exist
                    missing_cols = [col for col in candlestick_cols if col not in columns]
                    if missing_cols:
                        logger.error(f"Missing candlestick columns: {missing_cols}")
                        return None
                    
                    # For candlestick, y_col should be the Close column
                    y_col = "Close"
                    
                if not x_col and columns:
                    x_col = columns[0]
                    logger.info(f"Auto-detected x_col: {x_col}")
                if not y_col and len(columns) > 1:
                    y_col = columns[1]
                    logger.info(f"Auto-detected y_col: {y_col}")
                elif not y_col and columns:
                    y_col = columns[0]
                    logger.info(f"Using single column for y_col: {y_col}")
            
            if not x_col or not y_col:
                logger.error(f"Could not determine x and y columns. x_col: {x_col}, y_col: {y_col}")
                return None
            
            processed_result = {
                "data": data,
                "x_col": x_col,
                "y_col": y_col,
                "columns": list(data[0].keys()) if data and isinstance(data[0], dict) else []
            }
            
            logger.info(f"Successfully processed chart data: {len(data)} rows, x_col: {x_col}, y_col: {y_col}")
            return processed_result
            
        except Exception as e:
            logger.error(f"Error processing chart data: {e}")
            return None
    
    def _create_bar_chart(self, processed_data: Dict[str, Any], title: str) -> go.Figure:
        """Create a bar chart with dark theme."""
        df = pd.DataFrame(processed_data["data"])
        x_col = processed_data["x_col"]
        y_col = processed_data["y_col"]
        
        # Format axis labels
        x_label = self._format_column_name(x_col)
        y_label = self._format_column_name(y_col)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df[x_col],
            y=df[y_col],
            marker_color=self.colors[0],
            marker_line=dict(color='rgba(255,255,255,0.3)', width=1),
            hovertemplate=f'<b>{x_label}: %{{x}}</b><br>{y_label}: %{{y}}<extra></extra>',
            name=f"{y_label} by {x_label}"
        ))
        
        # Apply theme and set axis titles
        self._apply_dark_theme(fig, title)
        fig.update_xaxes(title_text=x_label)
        fig.update_yaxes(title_text=y_label)
        
        return fig
    
    def _create_pie_chart(self, processed_data: Dict[str, Any], title: str) -> go.Figure:
        """Create a pie chart with dark theme."""
        df = pd.DataFrame(processed_data["data"])
        x_col = processed_data["x_col"]
        y_col = processed_data["y_col"]
        
        fig = go.Figure()
        fig.add_trace(go.Pie(
            labels=df[x_col],
            values=df[y_col],
            marker=dict(
                colors=self.colors,
                line=dict(color='rgba(255,255,255,0.1)', width=1)
            ),
            textfont=dict(color='white', size=12),
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
            pull=0.05,
            name=title
        ))
        
        self._apply_dark_theme(fig, title)
        return fig
    
    def _create_line_chart(self, processed_data: Dict[str, Any], title: str) -> go.Figure:
        """Create a line chart with dark theme."""
        df = pd.DataFrame(processed_data["data"])
        x_col = processed_data["x_col"]
        y_col = processed_data["y_col"]
        
        # Format axis labels
        x_label = self._format_column_name(x_col)
        y_label = self._format_column_name(y_col)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode='lines+markers',
            line=dict(color=self.colors[0], width=3),
            marker=dict(
                color=self.colors[1], 
                size=8,
                line=dict(color='white', width=1)
            ),
            hovertemplate=f'<b>{x_label}: %{{x}}</b><br>{y_label}: %{{y}}<extra></extra>',
            name=f"{y_label} over {x_label}"
        ))
        
        # Apply theme and set axis titles
        self._apply_dark_theme(fig, title)
        fig.update_xaxes(title_text=x_label)
        fig.update_yaxes(title_text=y_label)
        
        return fig
    
    def _create_scatter_chart(self, processed_data: Dict[str, Any], title: str) -> go.Figure:
        """Create a scatter chart with dark theme."""
        df = pd.DataFrame(processed_data["data"])
        x_col = processed_data["x_col"]
        y_col = processed_data["y_col"]
        
        # Format axis labels
        x_label = self._format_column_name(x_col)
        y_label = self._format_column_name(y_col)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode='markers',
            marker=dict(
                color=self.colors[0],
                size=10,
                line=dict(color='white', width=1),
                opacity=0.8
            ),
            hovertemplate=f'<b>{x_label}: %{{x}}</b><br>{y_label}: %{{y}}<extra></extra>',
            name=f"{y_label} vs {x_label}"
        ))
        
        # Apply theme and set axis titles
        self._apply_dark_theme(fig, title)
        fig.update_xaxes(title_text=x_label)
        fig.update_yaxes(title_text=y_label)
        
        return fig
    
    def _create_candlestick_chart(self, processed_data: Dict[str, Any], title: str) -> go.Figure:
        """Create a candlestick chart with dark theme."""
        df = pd.DataFrame(processed_data["data"])
        
        # For candlestick charts, we expect Date, Open, High, Low, Close columns
        date_col = processed_data.get("x_col", "Date")
        
        # Format axis labels
        date_label = self._format_column_name(date_col)
        
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df[date_col],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="OHLC",
            increasing=dict(
                fillcolor=self.colors[1],  # Green for increasing
                line=dict(color=self.colors[1], width=1)
            ),
            decreasing=dict(
                fillcolor=self.colors[3],  # Red for decreasing  
                line=dict(color=self.colors[3], width=1)
            ),
            text=[f"Open: {row['Open']}<br>High: {row['High']}<br>Low: {row['Low']}<br>Close: {row['Close']}" 
                  for _, row in df.iterrows()],
            hoverinfo='text+x'
        ))
        
        # Apply theme and set axis titles
        self._apply_dark_theme(fig, title)
        fig.update_xaxes(title_text=date_label)
        fig.update_yaxes(title_text="Price")
        
        # Remove range slider for cleaner look
        fig.update_layout(xaxis_rangeslider_visible=False)
        
        return fig
    
    def _apply_dark_theme(self, fig: go.Figure, title: str):
        """Apply dark theme styling to a Plotly figure."""
        fig.update_layout(
            font=dict(
                size=12, 
                color=self.dark_theme["text_color"], 
                family=self.dark_theme["font_family"]
            ),
            plot_bgcolor=self.dark_theme["background_color"],
            paper_bgcolor=self.dark_theme["background_color"],
            margin=dict(l=40, r=40, t=60, b=40),
            title=dict(
                text=title,
                font=dict(color=self.dark_theme["text_color"], size=16),
                x=0.5
            ),
            xaxis=dict(
                gridcolor=self.dark_theme["grid_color"],
                title=dict(font=dict(color=self.dark_theme["text_color"], size=12)),
                tickfont=dict(color=self.dark_theme["text_color"], size=10),
                linecolor='rgba(255,255,255,0.4)'
            ),
            yaxis=dict(
                gridcolor=self.dark_theme["grid_color"],
                title=dict(font=dict(color=self.dark_theme["text_color"], size=12)),
                tickfont=dict(color=self.dark_theme["text_color"], size=10),
                linecolor='rgba(255,255,255,0.4)'
            ),
            legend=dict(
                font=dict(color=self.dark_theme["text_color"], size=10),
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='rgba(255,255,255,0.2)',
                borderwidth=1
            ),
            hoverlabel=dict(
                bgcolor='rgba(15,15,35,0.9)',
                bordercolor='rgba(255,255,255,0.3)',
                font=dict(color=self.dark_theme["text_color"])
            )
        )


def validate_chart_data(data: Any) -> bool:
    """
    Validate that data is suitable for chart creation.
    
    Args:
        data: Data to validate
        
    Returns:
        True if data is valid, False otherwise
    """
    if not data:
        return False
    
    if isinstance(data, list) and len(data) > 0:
        # Check if it's a list of dictionaries
        if isinstance(data[0], dict) and len(data[0]) >= 2:
            return True
    
    if isinstance(data, dict) and "data" in data:
        return validate_chart_data(data["data"])
    
    return False


def get_chart_summary(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get a summary of chart data for display purposes.
    
    Args:
        chart_data: Chart data to summarize
        
    Returns:
        Dict containing summary information
    """
    try:
        if "data" in chart_data and isinstance(chart_data["data"], list):
            data = chart_data["data"]
            
            return {
                "row_count": len(data),
                "columns": list(data[0].keys()) if data else [],
                "column_count": len(data[0].keys()) if data else 0,
                "x_column": chart_data.get("x", "auto-detected"),
                "y_column": chart_data.get("y", "auto-detected")
            }
        
        return {
            "row_count": 0,
            "columns": [],
            "column_count": 0,
            "x_column": "unknown",
            "y_column": "unknown"
        }
        
    except Exception as e:
        logger.error(f"Error getting chart summary: {e}")
        return {
            "error": str(e)
        }
