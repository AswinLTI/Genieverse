"""
Main Streamlit application for Genieverse.
Refactored with modular architecture for better maintainability and readability.
"""

import streamlit as st
import logging
import os
import json
import plotly.graph_objects as go
from typing import Optional

# Import custom modules
from config import APP_CONFIG, LOGGING_CONFIG, get_api_token, validate_config
from api_client import BlueverseAPIClient
from dashboard_manager import DashboardManager
from ui_components import UIComponents
from chart_utils import ChartBuilder
from response_processor import ResponseProcessor

# Voice input imports
from streamlit_mic_recorder import mic_recorder, speech_to_text

# Text-to-speech imports
import pyttsx3
import threading
import time

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]),
    format=LOGGING_CONFIG["format"]
)
logger = logging.getLogger(LOGGING_CONFIG["logger_name"])

# Set page configuration
st.set_page_config(page_title="Genieverse", layout="wide")

# Add header with Genie image and title
col1, col2 = st.columns([1, 5])
with col1:
    st.image("static/genie.png", width=120)
with col2:
    st.markdown("<h1>Genieverse</h1>", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    logger.debug("Initializing session state")
    
    if "api_client" not in st.session_state:
        st.session_state["api_client"] = None
    
    if "history" not in st.session_state:
        st.session_state["history"] = []
    
    # Voice input session state variables
    if "is_recording" not in st.session_state:
        st.session_state["is_recording"] = False
    if "recorded_text" not in st.session_state:
        st.session_state["recorded_text"] = ""
    if "last_query_completed" not in st.session_state:
        st.session_state["last_query_completed"] = False
    
    # Text-to-speech session state variables
    if "is_speaking" not in st.session_state:
        st.session_state["is_speaking"] = False
    if "tts_engine" not in st.session_state:
        st.session_state["tts_engine"] = None
    if "engine_busy" not in st.session_state:
        st.session_state["engine_busy"] = False
    if "last_response_text" not in st.session_state:
        st.session_state["last_response_text"] = ""
    if "auto_speak_on_voice" not in st.session_state:
        st.session_state["auto_speak_on_voice"] = True
    if "speech_start_time" not in st.session_state:
        st.session_state["speech_start_time"] = time.time()
    
    # Auto-initialize API client with token from environment
    if st.session_state["api_client"] is None:
        api_token = get_api_token()
        if api_token:
            try:
                st.session_state["api_client"] = BlueverseAPIClient(api_token)
                logger.info("API client auto-initialized from environment")
            except Exception as e:
                logger.error(f"Failed to initialize API client: {e}")
    
    logger.info("Session state initialized")


def ask_api(query: str) -> str:
    """Send query to API and process response with routing"""
    logger.debug(f"Processing query: {query}")
    
    if not st.session_state["api_client"]:
        return "❌ API client not configured. Please set your BLUEVERSE_API_TOKEN in .env file or use the sidebar."
    
    try:
        # Send query to API (routing is handled internally)
        result = st.session_state["api_client"].send_query(query)
        
        if not result["success"]:
            return f"❌ API Error: {result['error']}"
        
        api_response = result["data"]
        api_used = result.get("api_used", "unknown")
        
        # Add routing information to the response
        routing_info = ""
        if api_used == "main":
            routing_info = "🔹 *Routed to Main API (Simple Query)*\n\n"
        elif api_used == "json_generator":
            routing_info = "📊 *Routed to JSON Generator API (Chart/Table Query)*\n\n"
        elif api_used == "dashboard":
            routing_info = "🚀 *Creating Live Dashboard*\n\n"
        
        # Extract chart data if available
        chart_data = None
        chart_created = False
        
        # Always try to extract chart data regardless of API used
        chart_data = extract_chart_data(api_response)
        
        if chart_data:
            try:
                fig = None
                
                # Handle JSON Generator format using chart builder
                if "json_generator_data" in chart_data:
                    chart_builder = ChartBuilder()
                    chart_info = chart_data["json_generator_data"]
                    chart_type = chart_info.get("chart_type", "bar")
                    
                    # Generate context-aware title from the original query
                    context_title = extract_context_from_query(user_input, chart_type, chart_info)
                    
                    # Debug logging
                    logger.info(f"Creating chart of type: {chart_type}")
                    logger.info(f"Generated title: {context_title}")
                    logger.info(f"Chart data keys: {list(chart_info.keys())}")
                    logger.info(f"Data sample: {chart_info.get('data', [])[:2] if chart_info.get('data') else 'No data'}")
                    
                    fig = chart_builder.create_chart(chart_info, chart_type, context_title)
                    if fig:
                        st.session_state["chart"] = fig
                        chart_created = True
                        logger.info("JSON Generator chart created and stored successfully")
                        
                        # Check if there are multiple charts from dashboard response
                        if "multiple_charts" in chart_data:
                            all_charts = chart_data["multiple_charts"]
                            st.session_state["multiple_charts"] = []
                            
                            for i, chart_info_multi in enumerate(all_charts):
                                chart_type_multi = chart_info_multi.get("chart_type", "bar")
                                chart_title_multi = extract_context_from_query(user_input, chart_type_multi, chart_info_multi)
                                
                                chart_fig = chart_builder.create_chart(chart_info_multi, chart_type_multi, chart_title_multi)
                                if chart_fig:
                                    st.session_state["multiple_charts"].append(chart_fig)
                            
                            logger.info(f"Created {len(st.session_state['multiple_charts'])} dashboard charts")
                    else:
                        logger.error("ChartBuilder returned None - chart creation failed")
                
                # Handle legacy chart_json format
                elif "chart_json" in chart_data:
                    chart_json = chart_data["chart_json"]
                    if isinstance(chart_json, str):
                        fig_dict = json.loads(chart_json)
                        fig = go.Figure(fig_dict)
                    else:
                        fig = chart_json
                    st.session_state["chart"] = fig
                    chart_created = True
                    logger.info("Legacy chart data extracted and stored")
                
                # Direct chart data format (fallback)
                else:
                    logger.info("Attempting direct chart creation from API response")
                    chart_builder = ChartBuilder()
                    # Try to determine chart type from response or default to bar
                    chart_type = api_response.get("chart_type", "bar")
                    fig = chart_builder.create_chart(api_response, chart_type)
                    if fig:
                        st.session_state["chart"] = fig
                        chart_created = True
                        logger.info("Direct chart creation successful")
                    
            except Exception as e:
                logger.error(f"Error processing chart data: {e}")
                import traceback
                logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Process and return text response with routing info
        response_processor = ResponseProcessor()
        if api_used == "dashboard":
            # For dashboard creation, check if we also created charts
            if chart_created:
                multiple_charts = st.session_state.get("multiple_charts", [])
                if len(multiple_charts) > 1:
                    response_text = f"✅ Dashboard created with {len(multiple_charts)} interactive charts!"
                elif chart_created:
                    response_text = "✅ Dashboard created with interactive chart!"
                else:
                    response_text = response_processor.process_response(api_response)
            else:
                response_text = response_processor.process_response(api_response)
        elif chart_created and api_used == "json_generator":
            # If we successfully created a chart from JSON Generator, provide a clean message
            chart_info = chart_data.get("json_generator_data", {})
            chart_type = chart_info.get("chart_type", "chart")
            data_count = len(chart_info.get("data", []))
            response_text = f"✅ Successfully generated {chart_type} chart with {data_count} data points."
        else:
            # Use the original response processing
            response_text = response_processor.process_response(api_response)
        
        final_response = response_text #routing_info + response_text
        
        logger.info(f"Query processed successfully via {api_used} API")
        return final_response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return f"❌ Error: {str(e)}. Please try again or check your API connection."


def extract_chart_data(api_response):
    """Extract chart data from API response - keeping original logic"""
    try:
        chart_data = {}
        
        # Try to extract chart data from various response formats
        if isinstance(api_response, dict):
            # Handle JSON Generator response format
            if "status" in api_response and api_response.get("status") == "success":
                if "data" in api_response and api_response["data"]:
                    chart_data["json_generator_data"] = api_response
                    return chart_data
            
            # Try to find embedded JSON in string fields
            for field in ["response", "message", "content", "data", "result"]:
                if field in api_response and isinstance(api_response[field], str):
                    try:
                        parsed_json = json.loads(api_response[field])
                        if isinstance(parsed_json, dict):
                            # Handle dashboard response with multiple charts
                            if "charts" in parsed_json and isinstance(parsed_json["charts"], list):
                                # Return the first chart for now (we can enhance this later)
                                if parsed_json["charts"]:
                                    first_chart = parsed_json["charts"][0]
                                    first_chart["status"] = "success"  # Add status for compatibility
                                    chart_data["json_generator_data"] = first_chart
                                    chart_data["multiple_charts"] = parsed_json["charts"]  # Store all charts
                                    return chart_data
                            
                            # Handle single chart response
                            elif "status" in parsed_json and parsed_json.get("status") == "success":
                                if "data" in parsed_json:
                                    chart_data["json_generator_data"] = parsed_json
                                    return chart_data
                    except json.JSONDecodeError:
                        continue
                elif field in api_response and isinstance(api_response[field], dict):
                    # Check nested structure
                    nested = api_response[field]
                    for nested_field in ["response", "message", "content", "data", "result"]:
                        if nested_field in nested and isinstance(nested[nested_field], str):
                            try:
                                parsed_json = json.loads(nested[nested_field])
                                if isinstance(parsed_json, dict):
                                    # Handle dashboard response with multiple charts
                                    if "charts" in parsed_json and isinstance(parsed_json["charts"], list):
                                        if parsed_json["charts"]:
                                            first_chart = parsed_json["charts"][0]
                                            first_chart["status"] = "success"
                                            chart_data["json_generator_data"] = first_chart
                                            chart_data["multiple_charts"] = parsed_json["charts"]
                                            return chart_data
                                    
                                    # Handle single chart response
                                    elif "status" in parsed_json and parsed_json.get("status") == "success":
                                        if "data" in parsed_json:
                                            chart_data["json_generator_data"] = parsed_json
                                            return chart_data
                            except json.JSONDecodeError:
                                continue
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting chart data: {e}")
        return None


def extract_context_from_query(query: str, chart_type: str, chart_info: dict) -> str:
    """Extract contextual information from the user query to create better chart titles"""
    query_lower = query.lower()
    
    # Extract company/stock names
    stock_patterns = ["tcs", "stock", "share", "equity"]
    time_patterns = ["2018", "jan", "january", "feb", "february", "mar", "march", 
                    "apr", "april", "may", "jun", "june", "jul", "july", "aug", "august",
                    "sep", "september", "oct", "october", "nov", "november", "dec", "december"]
    
    # Try to extract company name
    company = ""
    if "tcs" in query_lower:
        company = "TCS"
    elif "stock" in query_lower or "share" in query_lower:
        # Look for company name before "stock" or "share"
        words = query.split()
        for i, word in enumerate(words):
            if word.lower() in ["stock", "share", "shares"]:
                if i > 0:
                    company = words[i-1].upper()
                break
    
    # Try to extract time period
    time_period = ""
    for pattern in time_patterns:
        if pattern in query_lower:
            if pattern == "2018":
                time_period = "2018"
            elif pattern in ["jan", "january"]:
                time_period = "January 2018" if "2018" in query_lower else "January"
            elif pattern in ["jul", "july"]:
                time_period = "July 2018" if "2018" in query_lower else "July"
            # Add more months as needed
    
    # Get data columns for context
    x_col = chart_info.get("x", "")
    y_col = chart_info.get("y", "")
    
    # Format column names
    if isinstance(y_col, list):
        y_display = ", ".join(y_col)
    else:
        y_display = y_col.replace("_", " ").title()
    
    x_display = x_col.replace("_", " ").title()
    
    # Generate contextual title
    if chart_type == "candlestick":
        if company and time_period:
            return f"{company} Stock Price - {time_period}"
        elif company:
            return f"{company} Stock Price"
        elif time_period:
            return f"Stock Price - {time_period}"
        else:
            return "Stock Price Chart"
    elif chart_type == "line":
        if company and time_period:
            return f"{company} {y_display} - {time_period}"
        elif company:
            return f"{company} {y_display} over {x_display}"
        elif time_period:
            return f"{y_display} over {x_display} - {time_period}"
        else:
            return f"{y_display} over {x_display}"
    elif chart_type == "scatter":
        if company:
            return f"{company} {y_display} vs {x_display}"
        else:
            return f"{y_display} vs {x_display}"
    elif chart_type == "bar":
        # Handle customer spend scenarios
        if "customer" in query_lower and "spend" in query_lower:
            return "Top Customers by Spend"
        elif "customer" in x_display.lower():
            return f"Top Customers by {y_display}"
        elif company:
            return f"{company} {y_display} by {x_display}"
        else:
            return f"{y_display} by {x_display}"
    elif chart_type == "pie":
        # Handle category scenarios
        if "categor" in query_lower:
            return "Product Categories Distribution"
        elif "product" in query_lower:
            return "Product Distribution"
        else:
            return f"Distribution of {y_display}"
    else:
        return f"{y_display} Chart"


def extract_profile_data(api_response):
    """Extract structured profiling data from API response"""
    try:
        # Handle different response formats
        if isinstance(api_response, dict):
            # Check if it's already a profile format
            if "profile" in api_response and "column_profiles" in api_response.get("profile", {}):
                return api_response
            
            # Check if it's nested in response field
            if "response" in api_response:
                try:
                    import json
                    parsed = json.loads(api_response["response"])
                    if "profile" in parsed and "column_profiles" in parsed.get("profile", {}):
                        return parsed
                except (json.JSONDecodeError, TypeError):
                    pass
        
        # Try to parse as JSON string
        if isinstance(api_response, str):
            try:
                import json
                parsed = json.loads(api_response)
                if "profile" in parsed and "column_profiles" in parsed.get("profile", {}):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting profile data: {e}")
        return None


def display_interactive_profile(profile_data, table_name):
    """Display interactive profiling results with charts and metrics"""
    try:
        profile = profile_data.get("profile", {})
        table_name_from_data = profile.get("table_name", table_name)
        row_count = profile.get("row_count", 0)
        column_profiles = profile.get("column_profiles", {})
        anomalies = profile.get("anomalies", [])
        
        # Header section
        st.markdown(f"## 📊 Profile Report: `{table_name_from_data}`")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📝 Total Rows", f"{row_count:,}")
        with col2:
            st.metric("📋 Total Columns", len(column_profiles))
        with col3:
            valid_columns = sum(1 for col_data in column_profiles.values() 
                              if not isinstance(col_data, dict) or "error" not in col_data)
            st.metric("✅ Valid Columns", valid_columns)
        with col4:
            error_columns = sum(1 for col_data in column_profiles.values() 
                              if isinstance(col_data, dict) and "error" in col_data)
            st.metric("❌ Error Columns", error_columns)
        
        # Data type distribution chart
        create_datatype_chart(column_profiles)
        
        # Detailed column analysis
        st.markdown("### 📋 Column Details")
        
        # Filter out error columns for main analysis
        valid_columns_data = {col: data for col, data in column_profiles.items() 
                            if not (isinstance(data, dict) and "error" in data)}
        
        if valid_columns_data:
            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["📊 Overview", "🔍 Data Quality", "📈 Distributions"])
            
            with tab1:
                display_column_overview(valid_columns_data, row_count)
            
            with tab2:
                display_data_quality_analysis(valid_columns_data, row_count)
            
            with tab3:
                display_column_distributions(valid_columns_data)
        
        # Error columns section
        error_columns_data = {col: data for col, data in column_profiles.items() 
                            if isinstance(data, dict) and "error" in data}
        
        if error_columns_data:
            st.markdown("### ⚠️ Column Errors")
            for col_name, error_info in error_columns_data.items():
                with st.expander(f"❌ {col_name}", expanded=False):
                    st.error(error_info.get("error", "Unknown error"))
        
        # Anomalies section
        if anomalies:
            st.markdown("### 🚨 Data Quality Anomalies")
            for anomaly in anomalies:
                st.warning(f"⚠️ {anomaly}")
        else:
            st.success("✅ No data quality anomalies detected!")
            
    except Exception as e:
        st.error(f"Error displaying profile: {str(e)}")
        logger.error(f"Profile display error: {e}")


def create_datatype_chart(column_profiles):
    """Create a chart showing data type distribution"""
    try:
        # Count data types
        type_counts = {}
        for col_name, col_data in column_profiles.items():
            if isinstance(col_data, dict) and "data_type" in col_data:
                data_type = col_data["data_type"]
                type_counts[data_type] = type_counts.get(data_type, 0) + 1
        
        if type_counts:
            import plotly.graph_objects as go
            
            fig = go.Figure(data=[
                go.Pie(
                    labels=list(type_counts.keys()),
                    values=list(type_counts.values()),
                    hole=0.4,
                    textfont=dict(color='white', size=12),
                    textinfo='label+percent+value',
                    marker=dict(
                        colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'],
                        line=dict(color='rgba(255,255,255,0.1)', width=1)
                    )
                )
            ])
            
            fig.update_layout(
                title=dict(
                    text="Data Type Distribution",
                    font=dict(color='white', size=16),
                    x=0.5
                ),
                font=dict(color='white', size=12),
                plot_bgcolor='#0e1117',
                paper_bgcolor='#0e1117',
                margin=dict(l=20, r=20, t=60, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        logger.error(f"Error creating datatype chart: {e}")


def display_column_overview(column_profiles, total_rows):
    """Display column overview table"""
    try:
        import pandas as pd
        
        overview_data = []
        for col_name, col_data in column_profiles.items():
            if isinstance(col_data, dict) and "data_type" in col_data:
                overview_data.append({
                    "Column": col_name,
                    "Data Type": col_data.get("data_type", "unknown"),
                    "Non-Null Count": f"{col_data.get('non_null_count', 0):,}",
                    "Null %": f"{col_data.get('null_percentage', 0):.1f}%",
                    "Distinct Values": f"{col_data.get('distinct_count', 0):,}",
                    "Uniqueness %": f"{(col_data.get('distinct_count', 0) / total_rows * 100):.1f}%" if total_rows > 0 else "0%"
                })
        
        if overview_data:
            df = pd.DataFrame(overview_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    except Exception as e:
        logger.error(f"Error displaying column overview: {e}")
        st.error("Error displaying column overview")


def display_data_quality_analysis(column_profiles, total_rows):
    """Display data quality metrics and charts"""
    try:
        # Calculate quality metrics
        completeness_data = []
        uniqueness_data = []
        
        for col_name, col_data in column_profiles.items():
            if isinstance(col_data, dict) and "data_type" in col_data:
                completeness = 100 - col_data.get("null_percentage", 0)
                uniqueness = (col_data.get("distinct_count", 0) / total_rows * 100) if total_rows > 0 else 0
                
                completeness_data.append({"Column": col_name, "Completeness": completeness})
                uniqueness_data.append({"Column": col_name, "Uniqueness": uniqueness})
        
        if completeness_data:
            # Completeness chart
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Data Completeness")
                import plotly.graph_objects as go
                
                fig = go.Figure(data=[
                    go.Bar(
                        x=[item["Completeness"] for item in completeness_data],
                        y=[item["Column"] for item in completeness_data],
                        orientation='h',
                        marker_color='#1f77b4',
                        text=[f"{item['Completeness']:.1f}%" for item in completeness_data],
                        textposition='inside'
                    )
                ])
                
                fig.update_layout(
                    title="Data Completeness by Column",
                    xaxis_title="Completeness %",
                    font=dict(color='white'),
                    plot_bgcolor='#0e1117',
                    paper_bgcolor='#0e1117',
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("#### Data Uniqueness")
                
                fig2 = go.Figure(data=[
                    go.Bar(
                        x=[item["Uniqueness"] for item in uniqueness_data],
                        y=[item["Column"] for item in uniqueness_data],
                        orientation='h',
                        marker_color='#ff7f0e',
                        text=[f"{item['Uniqueness']:.1f}%" for item in uniqueness_data],
                        textposition='inside'
                    )
                ])
                
                fig2.update_layout(
                    title="Data Uniqueness by Column",
                    xaxis_title="Uniqueness %",
                    font=dict(color='white'),
                    plot_bgcolor='#0e1117',
                    paper_bgcolor='#0e1117',
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=400
                )
                
                st.plotly_chart(fig2, use_container_width=True)
    
    except Exception as e:
        logger.error(f"Error displaying data quality analysis: {e}")
        st.error("Error displaying data quality analysis")


def display_column_distributions(column_profiles):
    """Display detailed column statistics"""
    try:
        # Group columns by data type
        numeric_cols = []
        string_cols = []
        datetime_cols = []
        
        for col_name, col_data in column_profiles.items():
            if isinstance(col_data, dict) and "data_type" in col_data:
                data_type = col_data["data_type"]
                if data_type in ["integer", "float", "numeric"]:
                    numeric_cols.append((col_name, col_data))
                elif data_type == "string":
                    string_cols.append((col_name, col_data))
                elif data_type in ["datetime", "date", "timestamp"]:
                    datetime_cols.append((col_name, col_data))
        
        # Display numeric columns
        if numeric_cols:
            st.markdown("#### 🔢 Numeric Columns")
            for col_name, col_data in numeric_cols:
                with st.expander(f"📊 {col_name}", expanded=False):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Min", f"{col_data.get('min_value', 'N/A')}")
                    with col2:
                        st.metric("Max", f"{col_data.get('max_value', 'N/A')}")
                    with col3:
                        st.metric("Mean", f"{col_data.get('mean_value', 'N/A'):.2f}" if col_data.get('mean_value') else "N/A")
                    with col4:
                        st.metric("Std Dev", f"{col_data.get('std_deviation', 'N/A'):.2f}" if col_data.get('std_deviation') else "N/A")
        
        # Display string columns
        if string_cols:
            st.markdown("#### 🔤 String Columns")
            for col_name, col_data in string_cols:
                with st.expander(f"📝 {col_name}", expanded=False):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Min Length", f"{col_data.get('min_length', 'N/A')}")
                    with col2:
                        st.metric("Max Length", f"{col_data.get('max_length', 'N/A')}")
                    with col3:
                        st.metric("Avg Length", f"{col_data.get('avg_length', 'N/A'):.1f}" if col_data.get('avg_length') else "N/A")
        
        # Display datetime columns
        if datetime_cols:
            st.markdown("#### 📅 DateTime Columns")
            for col_name, col_data in datetime_cols:
                with st.expander(f"📅 {col_name}", expanded=False):
                    st.info(f"DateTime column with {col_data.get('distinct_count', 0):,} distinct values")
    
    except Exception as e:
        logger.error(f"Error displaying column distributions: {e}")
        st.error("Error displaying column distributions")


def display_sidebar():
    """Display the sidebar with API configuration and navigation - matches api_app.py exactly"""
    # Initialize UI components for sidebar functionality
    ui_components = UIComponents()
    
    # Use the same sidebar implementation from api_app.py
    return ui_components.render_sidebar()


def render_recording_section(position="top"):
    """Render voice recording section"""
    key_suffix = "_top" if position == "top" else "_bottom"
    if st.session_state.is_recording:
        text = speech_to_text(
            language="en",
            just_once=False,
            key=f"voice_input{key_suffix}",
            use_container_width=False
        )
        
        if text:
            st.session_state.recorded_text = text
            user_input = text
            logger.info("Voice Generated Text:\n%s", user_input)
            st.session_state.is_recording = False
            st.rerun()


def initialize_tts_engine():
    """Initialize text-to-speech engine"""
    if st.session_state.tts_engine is None:
        try:
            engine = pyttsx3.init()
            
            # Set voice properties
            voices = engine.getProperty('voices')
            if voices:
                # Try to use a female voice if available
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
                else:
                    # Use the first available voice if no female voice found
                    engine.setProperty('voice', voices[0].id)
            
            # Set speech rate (slower for better clarity)
            engine.setProperty('rate', 150)
            # Set volume
            engine.setProperty('volume', 1.0)
            
            st.session_state.tts_engine = engine
            st.session_state.engine_busy = False  # Track engine state
            logger.info("TTS engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            st.session_state.tts_engine = None
            st.session_state.engine_busy = False


def speak_text(text: str, auto_speak: bool = False, force_voice_query: bool = False):
    """Speak the given text using TTS"""
    try:
        # Remove routing information from the text
        clean_text = remove_routing_info(text)
        # Clean the text for speaking (remove markdown, emojis, etc.)
        clean_text = clean_text_for_speech(clean_text)
        
        if not clean_text.strip():
            return
        
        # For voice queries, be more aggressive about starting new speech
        if force_voice_query:
            # Stop any current speech first
            try:
                stop_speaking()
                logger.info("Stopped previous speech for new voice query")
            except:
                pass
        elif st.session_state.get('is_speaking', False) and auto_speak:
            logger.info("Already speaking, skipping auto-speak")
            return
        
        # Always reset states before starting new speech
        st.session_state.is_speaking = True
        st.session_state.engine_busy = False
        
        # Use threading to avoid blocking and properly manage state
        import threading
        import time
        
        def speak_and_reset():
            try:
                logger.info(f"Starting speech: {clean_text[:50]}...")
                
                # Try Windows SAPI directly first
                try:
                    import win32com.client
                    speaker = win32com.client.Dispatch("SAPI.SpVoice")
                    speaker.Speak(clean_text)
                    logger.info(f"Completed speaking with SAPI: {clean_text[:50]}...")
                except ImportError:
                    # Fallback to pyttsx3 if win32com is not available
                    logger.info("win32com not available, trying pyttsx3...")
                    import pyttsx3
                    temp_engine = pyttsx3.init()
                    
                    # Apply settings
                    voices = temp_engine.getProperty('voices')
                    if voices:
                        for voice in voices:
                            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                                temp_engine.setProperty('voice', voice.id)
                                break
                        else:
                            temp_engine.setProperty('voice', voices[0].id)
                    
                    temp_engine.setProperty('rate', 150)
                    temp_engine.setProperty('volume', 1.0)
                    
                    # Use the temporary engine for speech
                    temp_engine.say(clean_text)
                    temp_engine.runAndWait()
                    
                    # Clean up
                    try:
                        temp_engine.stop()
                        del temp_engine
                    except:
                        pass
                    
                    logger.info(f"Completed speaking with pyttsx3: {clean_text[:50]}...")
                except Exception as e:
                    # Last resort: try Windows built-in SAPI via os.system
                    logger.info(f"pyttsx3 failed, trying system command: {e}")
                    import os
                    import tempfile
                    
                    # Create a VBS script to use Windows TTS
                    vbs_script = f'''
                    Set objVoice = CreateObject("SAPI.SpVoice")
                    objVoice.Speak "{clean_text.replace('"', '""')}"
                    '''
                    
                    # Write to temporary file and execute
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.vbs', delete=False) as f:
                        f.write(vbs_script)
                        vbs_file = f.name
                    
                    try:
                        os.system(f'cscript //nologo "{vbs_file}"')
                        logger.info(f"Completed speaking with VBS: {clean_text[:50]}...")
                    finally:
                        try:
                            os.unlink(vbs_file)
                        except:
                            pass
                
            except Exception as e:
                logger.error(f"Error during speech: {e}")
            finally:
                # Always reset states when done - use a delay to ensure it sticks
                time.sleep(0.5)
                try:
                    # Reset states in session if available
                    if hasattr(st.session_state, 'is_speaking'):
                        st.session_state.is_speaking = False
                    if hasattr(st.session_state, 'engine_busy'):
                        st.session_state.engine_busy = False
                    logger.info("TTS states reset after completion")
                except:
                    # If session state is not available, just log
                    logger.info("Could not access session state to reset, but speech completed")
        
        # Start speech in thread
        thread = threading.Thread(target=speak_and_reset, daemon=True)
        thread.start()
        
    except Exception as e:
        logger.error(f"Error in speak_text: {e}")
        st.session_state.is_speaking = False
        st.session_state.engine_busy = False


def test_audio_output():
    """Test audio output with different methods"""
    st.write("🔊 Testing audio output...")
    
    test_text = "Hello, this is an audio test. Can you hear me?"
    
    try:
        # Method 1: Windows SAPI via win32com
        st.write("Method 1: Trying Windows SAPI...")
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            
            # List available voices
            voices = speaker.GetVoices()
            st.write(f"Found {voices.Count} SAPI voices")
            
            speaker.Speak(test_text)
            st.success("✅ SAPI method completed - did you hear it?")
            return
        except Exception as e:
            st.error(f"❌ SAPI method failed: {e}")
    
        # Method 2: VBS Script
        st.write("Method 2: Trying VBS script...")
        try:
            import os
            import tempfile
            
            vbs_script = f'''
            Set objVoice = CreateObject("SAPI.SpVoice")
            objVoice.Speak "{test_text}"
            '''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.vbs', delete=False) as f:
                f.write(vbs_script)
                vbs_file = f.name
            
            os.system(f'cscript //nologo "{vbs_file}"')
            os.unlink(vbs_file)
            st.success("✅ VBS method completed - did you hear it?")
            return
        except Exception as e:
            st.error(f"❌ VBS method failed: {e}")
        
        # Method 3: pyttsx3
        st.write("Method 3: Trying pyttsx3...")
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.say(test_text)
            engine.runAndWait()
            st.success("✅ pyttsx3 method completed - did you hear it?")
        except Exception as e:
            st.error(f"❌ pyttsx3 method failed: {e}")
            
    except Exception as e:
        st.error(f"❌ All audio test methods failed: {e}")
    
    st.write("💡 **Troubleshooting tips:**")
    st.write("- Check if your speakers/headphones are connected")
    st.write("- Check system volume and audio output device")
    st.write("- Try running Windows Narrator to test SAPI")
    st.write("- Check if Windows Speech service is running")


def stop_speaking():
    """Stop the current speech"""
    try:
        logger.info("Attempting to stop speech...")
        
        # Try to stop Windows SAPI
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Speak("", 1)  # Interrupt current speech
            logger.info("Stopped SAPI speech")
        except Exception as e:
            logger.error(f"Could not stop SAPI: {e}")
        
        # Try to stop pyttsx3 if it was used
        if st.session_state.get('tts_engine'):
            try:
                st.session_state.tts_engine.stop()
                logger.info("Stopped pyttsx3 engine")
            except Exception as e:
                logger.error(f"Could not stop pyttsx3: {e}")
        
        # Force reset states
        st.session_state.is_speaking = False
        st.session_state.engine_busy = False
        logger.info("Speech stopped and states reset")
        
    except Exception as e:
        logger.error(f"Error stopping speech: {e}")
        # Force reset the speaking state even if stop fails
        st.session_state.is_speaking = False
        st.session_state.engine_busy = False


def remove_routing_info(text: str) -> str:
    """Remove routing information from response text before TTS"""
    import re
    
    # Remove routing lines that start with emojis
    routing_patterns = [
        r'🔹\s*\*?Routed to.*?\*?\n*',
        r'📊\s*\*?Routed to.*?\*?\n*', 
        r'🚀\s*\*?Creating Live Dashboard\*?\n*',
        r'🔹\s*Routed to.*?\n*',
        r'📊\s*Routed to.*?\n*',
        r'🚀\s*Creating.*?\n*'
    ]
    
    for pattern in routing_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Clean up extra newlines
    text = re.sub(r'\n+', '\n', text)
    text = text.strip()
    
    return text


def clean_text_for_speech(text: str) -> str:
    """Clean text for better speech synthesis"""
    import re
    
    # Remove markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
    text = re.sub(r'`(.*?)`', r'\1', text)        # Code
    text = re.sub(r'#{1,6}\s*', '', text)         # Headers
    
    # Remove emojis and special characters
    text = re.sub(r'[🔹📊🚀❌✅⚠️💬📋🎙️🔍📝📊📈🔢🔤📅]', '', text)
    
    # Remove URLs
    text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
    
    # Clean up extra spaces and newlines
    text = re.sub(r'\n+', '. ', text)
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def render_tts_button():
    """Render the text-to-speech control button"""
    if st.session_state.last_response_text:
        st.markdown("---")  # Add separator
        
        # Check if speaking state has been stuck for too long (auto-reset after 30 seconds)
        current_time = time.time()
        if not hasattr(st.session_state, 'speech_start_time'):
            st.session_state.speech_start_time = current_time
        
        # More aggressive timeout for better UX - reset after 20 seconds or if no recent activity
        if st.session_state.get('is_speaking', False):
            if current_time - st.session_state.speech_start_time > 20:  # 20 seconds timeout
                logger.info("TTS timeout - auto-resetting speaking state")
                st.session_state.is_speaking = False
                st.session_state.engine_busy = False
                st.session_state.speech_start_time = current_time
        else:
            st.session_state.speech_start_time = current_time
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            is_currently_speaking = st.session_state.get('is_speaking', False)
            if is_currently_speaking:
                if st.button("🔇 Stop Reading", key="stop_tts", help="Stop reading", type="secondary"):
                    stop_speaking()
                    st.rerun()
            else:
                if st.button("🔊 Read Aloud", key="start_tts", help="Read response aloud", type="primary"):
                    st.session_state.speech_start_time = current_time
                    speak_text(st.session_state.last_response_text, auto_speak=True)
                    st.rerun()
        
        with col2:
            # Auto-speak toggle for voice queries
            st.session_state.auto_speak_on_voice = st.checkbox(
                "🎙️ Auto-read responses for voice queries", 
                value=st.session_state.auto_speak_on_voice,
                key="auto_speak_toggle",
                help="Automatically read responses when using voice input"
            )
        
        with col3:
            # Reset TTS state button
            if st.button("🔄 Reset", key="reset_tts", help="Reset TTS state if stuck"):
                st.session_state.is_speaking = False
                st.session_state.engine_busy = False
                st.session_state.speech_start_time = current_time
                st.success("TTS state reset!")
                st.rerun()
        
        # Show current TTS status for debugging
        if st.session_state.get('is_speaking', False):
            st.info(f"🔊 Currently speaking... (Started {int(current_time - st.session_state.speech_start_time)}s ago)")
        
        # Add audio test button
        if st.button("🔊 Test Audio", key="test_audio", help="Test if your audio is working"):
            test_audio_output()


# Main execution - keeping the exact same structure as api_app.py
initialize_session_state()

# Display sidebar and get selected page
current_page = display_sidebar()

# Page routing - exactly like api_app.py
if current_page == "💬 Chat with Genie":
    st.markdown("<h2>💬 Chat with the Genie</h2>", unsafe_allow_html=True)
    st.markdown("Ask me anything about your data! I can help you analyze, visualize, and understand your database.")
    
    # Chat history display - exactly like api_app.py
    if st.session_state["history"]:
        for i, (role, msg, chart) in enumerate(st.session_state["history"]):
            avatar = "static/genie.png" if role == "assistant" else None
            with st.chat_message(role, avatar=avatar):
                st.write(msg)
                # Add TTS controls for assistant messages
                if role == "assistant" and msg:
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("🔊", key=f"tts_history_{i}", help="Read this response aloud"):
                            st.session_state.last_response_text = msg
                            speak_text(msg, auto_speak=True)
                            st.rerun()
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
    
    # Voice input section - top recorder (only before first query)
    if not st.session_state["history"] or not st.session_state.last_query_completed:
        if not st.session_state.is_recording:
            if st.button("🎙️ Try Voice instead", key="top_voice_btn"):
                st.session_state.is_recording = True
                st.rerun()
        render_recording_section(position="top")
    
    # User input - both typed and voice
    typed_input = st.chat_input("Type your question here...")
    
    # Prioritize voice text if present and track if it's a voice query
    was_voice_query = False
    if st.session_state.recorded_text:
        user_input = st.session_state.recorded_text
        was_voice_query = True
        st.session_state.recorded_text = ""  # Clear after using
    elif typed_input:
        user_input = typed_input
        was_voice_query = False
    else:
        user_input = None
    
    if user_input:
        # Reset any stuck TTS state before processing new query
        current_time = time.time()
        if st.session_state.get('is_speaking', False) and hasattr(st.session_state, 'speech_start_time'):
            if current_time - st.session_state.speech_start_time > 15:  # 15 seconds max for any speech
                logger.info("Resetting stuck TTS state before new query")
                st.session_state.is_speaking = False
                st.session_state.engine_busy = False
        
        # Set query completed flag
        st.session_state.last_query_completed = True
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Get AI response
        with st.chat_message("assistant", avatar="static/genie.png"):
            with st.spinner("Thinking..."):
                response = ask_api(user_input)
            st.write(response)
            
            # Store response text for TTS
            st.session_state.last_response_text = response
            
            # Check if this was a voice query and auto-speak is enabled
            if was_voice_query and st.session_state.auto_speak_on_voice:
                logger.info(f"Voice query detected - attempting auto-speak. Current state: is_speaking={st.session_state.get('is_speaking', False)}, engine_busy={st.session_state.get('engine_busy', False)}")
                speak_text(response, auto_speak=True, force_voice_query=True)
            elif was_voice_query:
                logger.info("Voice query detected but auto-speak is disabled")
            else:
                logger.info("Text query detected - no auto-speak")
            
            # Always show TTS controls
            render_tts_button()
            
            # Check for chart data and display it
            chart = st.session_state.get("chart", None)
            multiple_charts = st.session_state.get("multiple_charts", None)
            
            if multiple_charts and len(multiple_charts) > 1:
                # Display multiple charts in a dashboard layout
                st.markdown("### 📊 Dashboard Charts")
                
                if len(multiple_charts) == 2:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.plotly_chart(multiple_charts[0], use_container_width=True)
                    with col2:
                        st.plotly_chart(multiple_charts[1], use_container_width=True)
                else:
                    # For more than 2 charts, display in rows
                    for i in range(0, len(multiple_charts), 2):
                        if i + 1 < len(multiple_charts):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.plotly_chart(multiple_charts[i], use_container_width=True)
                            with col2:
                                st.plotly_chart(multiple_charts[i + 1], use_container_width=True)
                        else:
                            st.plotly_chart(multiple_charts[i], use_container_width=True)
            elif chart:
                # Display single chart
                st.plotly_chart(chart, use_container_width=True)
        
        # Add to history - exactly like api_app.py format (preserve chart for history)
        chart_for_history = st.session_state.get("chart", None)
        multiple_charts_for_history = st.session_state.get("multiple_charts", None)
        
        # For multiple charts, use the first one for history compatibility
        if multiple_charts_for_history and len(multiple_charts_for_history) > 0:
            chart_for_history = multiple_charts_for_history[0]
        
        st.session_state["history"].append(("user", user_input, None))
        st.session_state["history"].append(("assistant", response, chart_for_history))
        
        # Clear chart data from session state after adding to history
        if "chart" in st.session_state:
            del st.session_state["chart"]
        if "multiple_charts" in st.session_state:
            del st.session_state["multiple_charts"]
        
        # Clear chat input by rerunning
        st.rerun()
    
    # Voice input section - bottom recorder (after queries)
    if st.session_state.last_query_completed:
        if not st.session_state.is_recording:
            if st.button("🎙️ Try Voice instead", key="bottom_voice_btn"):
                st.session_state.is_recording = True
                st.rerun()
        render_recording_section(position="bottom")

elif current_page == "📊 Profiler & Quality Checks":
    st.header("📊 Data Profiler & Quality Checks")
    st.markdown("Run profiling & quality checks on your database tables to understand data quality and characteristics.")
    
    # API client check
    if not st.session_state.get("api_client"):
        st.warning("⚠️ Please configure your API token in the sidebar to use the profiler.")
    else:
        # Table input
        col1, col2 = st.columns([3, 1])
        with col1:
            table_name = st.text_input(
                "Table Name:",
                placeholder="Enter the name of the table to profile (e.g., customers, orders, products)",
                help="Enter the exact name of the table you want to profile"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            profile_button = st.button("🔍 Profile Table", type="primary")
        
        # Available tables button
        st.markdown("---")
        if st.button("📋 Show Available Tables"):
            api_client = st.session_state.get("api_client")
            with st.spinner("Fetching available tables..."):
                try:
                    query = "Show me all available tables in the database. List the table names."
                    response = api_client.send_query(query)
                    
                    st.subheader("📋 Available Tables")
                    
                    if response.get("success"):
                        response_processor = ResponseProcessor()
                        content = response_processor.process_response(response["data"])
                        st.markdown(content)
                    else:
                        st.error("Failed to fetch tables")
                        st.write("Error:", response.get("error", "Unknown error"))
                        
                except Exception as e:
                    st.error(f"Error fetching tables: {e}")
        
        # Profile table if requested
        if profile_button and table_name:
            api_client = st.session_state.get("api_client")
            with st.spinner(f"🔍 Profiling table '{table_name}'..."):
                try:
                    # Create profiling query
                    query = f"""Please analyze and profile the table '{table_name}'. 
                    
                    I need the following information in JSON format:
                    - Table name and total row count
                    - For each column: data type, null count, distinct values, min/max values (for numeric), length statistics (for strings)
                    - Any data quality issues or anomalies
                    
                    Return comprehensive profiling data for the table."""
                    
                    response = api_client.send_query(query)
                    
                    # Process and display results
                    if response and response.get("success"):
                        response_processor = ResponseProcessor()
                        content = response_processor.process_response(response["data"])
                        
                        # Try to parse JSON if the response contains structured profile data
                        profile_data = extract_profile_data(response["data"])
                        
                        if profile_data:
                            st.success("✅ Table profiling completed!")
                            display_interactive_profile(profile_data, table_name)
                        else:
                            st.success("✅ Table profiling completed!")
                            st.markdown(content)
                    else:
                        st.error(f"❌ Failed to profile table '{table_name}'")
                        if response:
                            st.write("Error:", response.get("error", "Unknown error"))
                    
                except Exception as e:
                    st.error(f"Error profiling table: {str(e)}")
        
        # Show example
        st.markdown("---")
        with st.expander("📋 Example Profile Data"):
            st.markdown("Here's what a table profile looks like:")
            
            example_data = {
                "table_name": "customers",
                "row_count": 10000,
                "columns": {
                    "customer_id": {
                        "data_type": "integer",
                        "null_count": 0,
                        "distinct_count": 10000,
                        "min_value": 1,
                        "max_value": 10000
                    },
                    "name": {
                        "data_type": "string", 
                        "null_count": 0,
                        "distinct_count": 9437,
                        "min_length": 7,
                        "max_length": 26,
                        "avg_length": 13.3
                    }
                }
            }
            
            st.json(example_data)

elif current_page == "🚀 Live Dashboard":
    # Use UI components for dashboard registry
    ui_components = UIComponents()
    ui_components.render_dashboard_registry()
    ui_components.render_help_section()
