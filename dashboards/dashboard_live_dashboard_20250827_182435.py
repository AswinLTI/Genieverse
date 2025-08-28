# Auto-generated Dashboard Page
# Created: 2025-08-27 18:24:35
# Dashboard ID: dash_20250827_182435

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import json
import os
import requests
import logging
from typing import Dict, Any, Optional

# Configure page
st.set_page_config(
    page_title="Live Dashboard - Genieverse",
    layout="wide"
)

# Dashboard configuration
DASHBOARD_CONFIG = {
    "title": "Live Dashboard",
    "dashboard_id": "dash_20250827_182435",
    "created": "2025-08-27T18:24:35.649769",
    "charts": [
    {
        "type": "bar",
        "title": "Bar Chart: Top 10 Customers By Spend",
        "description": "top 10 customers by spend",
        "query": "Create a bar chart for top 10 customers by spend"
    },
    {
        "type": "line",
        "title": "Line Chart: Top 10 Customers By Spend",
        "description": "top 10 customers by spend",
        "query": "Create a line chart for top 10 customers by spend"
    },
    {
        "type": "pie",
        "title": "Pie Chart: Product Categories",
        "description": "product categories",
        "query": "Create a pie chart for product categories"
    }
]
}

# API Configuration
API_BASE_URL = "https://blueverse-foundry.ltimindtree.com/chatservice/chat"
JSON_GENERATOR_SPACE_NAME = "Json_Generator_975a2dc0"
JSON_GENERATOR_FLOW_ID = "68ae94113d219c7a19e1446d"

class DashboardAPI:
    """API client for dashboard data"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_token}'
        }
    
    def get_chart_data(self, query: str) -> Dict[str, Any]:
        """Get chart data from JSON Generator API"""
        try:
            payload = {
                "query": query,
                "space_name": JSON_GENERATOR_SPACE_NAME,
                "flowId": JSON_GENERATOR_FLOW_ID
            }
            
            response = requests.post(
                API_BASE_URL,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return {"success": True, "data": result}
            else:
                return {"success": False, "error": f"API Error {response.status_code}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

def create_plotly_chart(chart_data: Dict[str, Any], chart_type: str, chart_title: str) -> go.Figure:
    """Create Plotly chart with dark theme"""
    try:
        # Extract data from various response formats
        data = None
        x_col = ""
        y_col = ""
        
        if isinstance(chart_data, dict):
            if "data" in chart_data and chart_data["data"]:
                data = chart_data["data"]
                x_col = chart_data.get("x", "")
                y_col = chart_data.get("y", "")
            elif "response" in chart_data:
                try:
                    parsed = json.loads(chart_data["response"])
                    if "data" in parsed:
                        data = parsed["data"]
                        x_col = parsed.get("x", "")
                        y_col = parsed.get("y", "")
                except:
                    pass
        
        if not data:
            return None
        
        # Auto-detect columns if not specified
        if isinstance(data, list) and data:
            columns = list(data[0].keys())
            if not x_col:
                x_col = columns[0]
            if not y_col:
                y_col = columns[1] if len(columns) > 1 else columns[0]
        
        df = pd.DataFrame(data)
        fig = go.Figure()
        
        if chart_type == "bar":
            fig.add_trace(go.Bar(
                x=df[x_col],
                y=df[y_col],
                marker_color='#4FC3F7',
                marker_line=dict(color='rgba(79, 195, 247, 0.8)', width=1),
                hovertemplate='<b>%{x}</b><br>Value: %{y}<extra></extra>',
                name=chart_title
            ))
            
        elif chart_type == "pie":
            colors = ['#4FC3F7', '#81C784', '#FFB74D', '#F06292', '#BA68C8', '#64B5F6', '#4DB6AC', '#A1C181']
            fig.add_trace(go.Pie(
                labels=df[x_col],
                values=df[y_col],
                marker=dict(colors=colors, line=dict(color='rgba(255,255,255,0.1)', width=1)),
                textfont=dict(color='white', size=12),
                textinfo='label+percent',
                hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
                pull=0.05,
                name=chart_title
            ))
            
        elif chart_type == "line":
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='lines+markers',
                line=dict(color='#4FC3F7', width=3),
                marker=dict(color='#81C784', size=8, line=dict(color='white', width=1)),
                hovertemplate='<b>%{x}</b><br>Value: %{y}<extra></extra>',
                name=chart_title
            ))
        
        # Apply dark theme
        fig.update_layout(
            font=dict(size=12, color='white', family='Arial, sans-serif'),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=40, r=40, t=60, b=40),
            title=dict(
                text=chart_title,
                font=dict(color='white', size=16),
                x=0.5
            ),
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.2)',
                title=dict(font=dict(color='white', size=12)),
                tickfont=dict(color='white', size=10),
                linecolor='rgba(255,255,255,0.4)'
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.2)',
                title=dict(font=dict(color='white', size=12)),
                tickfont=dict(color='white', size=10),
                linecolor='rgba(255,255,255,0.4)'
            ),
            legend=dict(
                font=dict(color='white', size=10),
                bgcolor='rgba(0,0,0,0.5)',
                bordercolor='rgba(255,255,255,0.2)',
                borderwidth=1
            )
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating chart: {e}")
        return None

def display_chart(chart_config: Dict[str, Any], api_client: DashboardAPI, key_suffix: str = ""):
    """Display a single chart"""
    try:
        chart_title = chart_config.get('title', 'Chart')
        chart_type = chart_config.get('type', 'bar')
        chart_query = chart_config.get('query', '')
        
        st.markdown(f"### {chart_title}")
        
        with st.spinner(f"Loading {chart_title}..."):
            # Get data from API
            response = api_client.get_chart_data(chart_query)
            
            if response.get("success"):
                chart_data = response["data"]
                
                # Process response to extract chart data
                processed_data = None
                if isinstance(chart_data, dict):
                    if "data" in chart_data and chart_data["data"]:
                        processed_data = chart_data
                    elif "response" in chart_data:
                        try:
                            parsed = json.loads(chart_data["response"])
                            if "data" in parsed:
                                processed_data = parsed
                        except:
                            pass
                
                if processed_data:
                    fig = create_plotly_chart(processed_data, chart_type, chart_title)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True, key=f"chart_{chart_title}_{key_suffix}")
                    else:
                        st.error("❌ Could not create chart from data")
                else:
                    st.error("❌ No valid chart data received")
                    with st.expander("Debug Info"):
                        st.json(response)
            else:
                st.error(f"❌ API Error: {response.get('error', 'Unknown error')}")
                
    except Exception as e:
        st.error(f"❌ Error displaying chart: {str(e)}")

def main():
    """Main dashboard function"""
    # Custom CSS for dark theme
    st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
    }
    .stMarkdown, .stText {
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown(f"# 🚀 {DASHBOARD_CONFIG['title']}")
    st.markdown("**Live Dashboard** - Real-time data visualization")
    
    # API Token input
    api_token = st.text_input(
        "🔑 API Token:", 
        type="password",
        help="Enter your Blueverse API token",
        value=os.getenv("BLUEVERSE_API_TOKEN", "")
    )
    
    if not api_token:
        st.warning("⚠️ Please enter your API token to load charts")
        st.stop()
    
    # Initialize API client
    api_client = DashboardAPI(api_token)
    
    # Refresh button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Refresh All Charts", key="refresh_all"):
            st.rerun()
    
    st.markdown("---")
    
    # Display charts
    charts = DASHBOARD_CONFIG['charts']
    
    if len(charts) == 1:
        # Single chart
        display_chart(charts[0], api_client, "single")
    elif len(charts) == 2:
        # Two charts side by side
        col1, col2 = st.columns(2)
        with col1:
            display_chart(charts[0], api_client, "left")
        with col2:
            display_chart(charts[1], api_client, "right")
    else:
        # Multiple charts in grid
        for i in range(0, len(charts), 2):
            if i + 1 < len(charts):
                col1, col2 = st.columns(2)
                with col1:
                    display_chart(charts[i], api_client, f"grid_{i}")
                with col2:
                    display_chart(charts[i + 1], api_client, f"grid_{i+1}")
            else:
                display_chart(charts[i], api_client, f"grid_{i}")
    
    # Footer
    st.markdown("---")
    st.markdown(f"**Dashboard ID:** {DASHBOARD_CONFIG['dashboard_id']}")
    st.markdown(f"**Created:** {DASHBOARD_CONFIG['created'][:19].replace('T', ' ')}")
    st.markdown("**Powered by:** Genieverse & Blueverse Foundry")

if __name__ == "__main__":
    main()
