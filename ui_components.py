"""
UI components module for reusable Streamlit interface elements.
Contains functions for creating consistent UI components across the application.
"""

import streamlit as st
import os
import logging
from typing import Dict, Any, List, Optional, Callable
from config import APP_CONFIG, PATHS
from dashboard_manager import DashboardManager
from api_client import BlueverseAPIClient

logger = logging.getLogger("genieverse.ui_components")


class UIComponents:
    """Collection of reusable UI components for the Streamlit app."""
    
    @staticmethod
    def render_header():
        """Render the application header with logo and title."""
        col1, col2 = st.columns([1, 5])
        
        with col1:
            genie_image_path = PATHS["genie_image"]
            if os.path.exists(genie_image_path):
                st.image(genie_image_path, width=120)
            else:
                st.markdown("🧞", unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"<h1>{APP_CONFIG['title']}</h1>", unsafe_allow_html=True)
    
    @staticmethod
    def render_sidebar() -> str:
        """
        Render the sidebar with navigation and configuration options.
        
        Returns:
            Selected page name
        """
        with st.sidebar:
            # Navigation
            st.subheader("Navigation")
            page = st.selectbox(
                "Select Page:",
                ["💬 Chat with Genie", "📊 Profiler & Quality Checks", "🚀 Live Dashboard"],
                key="current_page"
            )
            
            st.markdown("---")
            
            # API Token configuration
            UIComponents._render_api_config()
            
            st.markdown("---")
            
            # Page-specific controls
            UIComponents._render_page_controls(page)
        
        return page
    
    @staticmethod
    def _render_api_config():
        """Render API configuration section in sidebar."""
        st.subheader("API Settings")
        
        from config import get_api_token
        current_token = get_api_token()
        
        api_token = st.text_input(
            "Blueverse API Token:",
            value=current_token if current_token else "",
            type="password",
            help="Enter your Blueverse Foundry API token"
        )
        
        if st.button("Update API Token"):
            if api_token.strip():
                try:
                    st.session_state["api_client"] = BlueverseAPIClient(api_token.strip())
                    st.success("✅ API token updated successfully!")
                    logger.info("API token updated via sidebar")
                except Exception as e:
                    st.error(f"❌ Failed to update API token: {str(e)}")
            else:
                st.error("❌ Please enter a valid API token")
    
    @staticmethod
    def _render_page_controls(page: str):
        """
        Render page-specific controls in sidebar.
        
        Args:
            page: Current page name
        """
        if page == "💬 Chat with Genie":
            if st.button("🗑️ Clear Chat History"):
                st.session_state["history"] = []
                st.rerun()
        
        if page in ["💬 Chat with Genie", "🚀 Live Dashboard"]:
            if "current_dashboard" in st.session_state:
                if st.button("🚮 Clear Dashboard"):
                    del st.session_state["current_dashboard"]
                    st.rerun()
    
    @staticmethod
    def render_chat_interface():
        """Render the main chat interface."""
        st.header("💬 Chat with Genie")
        st.markdown("Ask questions about your data, create charts, or build live dashboards!")
        
        # API client check
        if not st.session_state.get("api_client"):
            st.warning("⚠️ Please configure your API token in the sidebar to start chatting.")
            return
        
        # Chat history
        UIComponents._render_chat_history()
        
        # Chat input
        UIComponents._render_chat_input()
    
    @staticmethod
    def _render_chat_history():
        """Render chat history."""
        history = st.session_state.get("history", [])
        
        if history:
            st.subheader("💬 Conversation History")
            for i, entry in enumerate(history):
                with st.expander(f"Query {i+1}: {entry['query'][:50]}...", expanded=(i == len(history) - 1)):
                    st.markdown(f"**You:** {entry['query']}")
                    st.markdown(f"**Genie:** {entry['response']}")
                    st.markdown(f"*{entry['timestamp']}*")
        else:
            st.info("💡 Start a conversation by asking a question below!")
    
    @staticmethod
    def _render_chat_input():
        """Render chat input and handle submission."""
        # Chat input
        user_query = st.text_area(
            "Ask your question:",
            placeholder="Examples:\n- Show me top 10 customers by revenue\n- Create a bar chart of sales by region\n- Build a dashboard with customer analytics",
            height=100,
            key="chat_input"
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            if st.button("🔮 Ask Genie", type="primary", use_container_width=True):
                if user_query.strip():
                    UIComponents._process_chat_query(user_query.strip())
                else:
                    st.error("Please enter a question!")
    
    @staticmethod
    def _process_chat_query(query: str):
        """
        Process a chat query and display results.
        
        Args:
            query: User query to process
        """
        api_client = st.session_state.get("api_client")
        if not api_client:
            st.error("API client not configured")
            return
        
        with st.spinner("🔮 Genie is thinking..."):
            try:
                # Send query to API
                response = api_client.send_query(query)
                
                # Process response
                from response_processor import ResponseProcessor
                processor = ResponseProcessor()
                formatted_response = processor.process_response(response)
                
                # Add to history
                import datetime
                history_entry = {
                    "query": query,
                    "response": formatted_response,
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "raw_response": response
                }
                
                if "history" not in st.session_state:
                    st.session_state["history"] = []
                
                st.session_state["history"].append(history_entry)
                
                # Display response
                st.success("Response received!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
                logger.error(f"Chat query error: {e}")
    
    @staticmethod
    def render_dashboard_registry():
        """Render the dashboard registry interface."""
        st.header("🚀 Live Dashboard Registry")
        st.markdown("View and manage all your created live dashboards")
        
        dashboard_manager = DashboardManager()
        registry = dashboard_manager.get_dashboard_registry()
        
        if registry:
            UIComponents._render_dashboard_list(registry, dashboard_manager)
        else:
            UIComponents._render_empty_dashboard_state(dashboard_manager)
        
        # Dashboard stats
        UIComponents._render_dashboard_stats(dashboard_manager)
    
    @staticmethod
    def _render_dashboard_list(registry: List[Dict[str, Any]], dashboard_manager: DashboardManager):
        """
        Render the list of dashboards.
        
        Args:
            registry: List of dashboard entries
            dashboard_manager: Dashboard manager instance
        """
        st.success(f"**{len(registry)} Dashboard(s) Available**")
        
        # Management buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("🔄 Refresh Registry", key="refresh_registry"):
                st.rerun()
        with col2:
            if st.button("📁 Open Pages Folder", key="open_folder"):
                pages_dir = PATHS["pages_dir"]
                st.info(f"📁 Pages folder: `{pages_dir}`")
        with col3:
            if st.button("🗑️ Clear Registry", key="clear_registry"):
                if st.checkbox("Confirm deletion", key="confirm_clear"):
                    if dashboard_manager.clear_registry():
                        st.success("Registry cleared!")
                        st.rerun()
                    else:
                        st.error("Failed to clear registry")
        
        st.markdown("---")
        
        # Display dashboards
        for i, dashboard in enumerate(reversed(registry)):
            UIComponents._render_dashboard_item(dashboard, len(registry) - 1 - i, dashboard_manager)
    
    @staticmethod
    def _render_dashboard_item(dashboard: Dict[str, Any], index: int, dashboard_manager: DashboardManager):
        """
        Render a single dashboard item.
        
        Args:
            dashboard: Dashboard entry
            index: Dashboard index
            dashboard_manager: Dashboard manager instance
        """
        title = dashboard.get('title', 'Unknown Dashboard')
        charts_count = len(dashboard.get('charts', []))
        
        with st.expander(f"📊 {title} - {charts_count} charts", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Created:** {dashboard['created'][:19].replace('T', ' ')}")
                
                # Check format type
                if "page_name" in dashboard:
                    # New Streamlit page format
                    st.write(f"**Page:** `{dashboard['page_name']}.py`")
                    st.write(f"**URL:** `{dashboard.get('url', 'N/A')}`")
                    st.write(f"**ID:** `{dashboard.get('dashboard_id', 'N/A')}`")
                else:
                    # Legacy format
                    st.write(f"**File:** `{dashboard.get('file_name', 'N/A')}`")
                
                # Charts info
                st.write("**Charts:**")
                for j, chart in enumerate(dashboard.get('charts', [])):
                    st.write(f"  {j+1}. {chart.get('title', 'Unknown')} ({chart.get('type', 'unknown')})")
            
            with col2:
                # Action buttons
                if "page_name" in dashboard:
                    # New format actions
                    if st.button(f"🚀 Open Dashboard", key=f"open_{index}"):
                        st.markdown(f"**Dashboard URL:** {dashboard.get('url', 'N/A')}")
                        st.info("The dashboard is now available in your Streamlit app sidebar!")
                    
                    if st.button(f"📋 Copy URL", key=f"copy_url_{index}"):
                        st.code(dashboard.get('url', 'N/A'))
                else:
                    # Legacy format actions
                    if st.button(f"▶️ Run Dashboard", key=f"run_{index}"):
                        file_path = dashboard.get('file_path', '')
                        if file_path and os.path.exists(file_path):
                            st.code(f"streamlit run \"{file_path}\"")
                            st.info("Copy the command above and run it in your terminal")
                        else:
                            st.error("Dashboard file not found")
                    
                    if st.button(f"📋 Copy Path", key=f"copy_{index}"):
                        st.code(dashboard.get('file_path', 'N/A'))
                
                if st.button(f"🗑️ Remove", key=f"remove_{index}"):
                    if dashboard_manager.remove_dashboard(index):
                        st.success("Dashboard removed from registry")
                        st.rerun()
                    else:
                        st.error("Failed to remove dashboard")
    
    @staticmethod
    def _render_empty_dashboard_state(dashboard_manager: DashboardManager):
        """
        Render UI for when no dashboards exist.
        
        Args:
            dashboard_manager: Dashboard manager instance
        """
        st.info("No live dashboards have been created yet.")
        st.markdown("""
        **To create a live dashboard:**
        1. Go to the "💬 Chat with Genie" page
        2. Ask to create a dashboard, for example:
           - "Create a live dashboard with a bar chart for top 10 customers by spend and a pie chart of product categories"
           - "Build a dashboard showing sales trends and customer distribution"
        3. The dashboard will be saved as a page and listed here
        """)
        
        # Sample dashboard creation
        st.markdown("---")
        if st.button("🧪 Create Sample Dashboard"):
            UIComponents._create_sample_dashboard(dashboard_manager)
    
    @staticmethod
    def _create_sample_dashboard(dashboard_manager: DashboardManager):
        """
        Create a sample dashboard for testing.
        
        Args:
            dashboard_manager: Dashboard manager instance
        """
        sample_config = {
            "title": "Sample Dashboard",
            "charts": [
                {
                    "type": "bar",
                    "title": "Sample Bar Chart",
                    "description": "sample data",
                    "query": "Create a bar chart showing sample sales data by region"
                },
                {
                    "type": "pie", 
                    "title": "Sample Pie Chart",
                    "description": "sample distribution",
                    "query": "Create a pie chart showing sample product category distribution"
                }
            ]
        }
        
        result = dashboard_manager.create_dashboard_from_query("Create sample dashboard")
        
        if result["success"]:
            st.success("Sample dashboard created!")
            st.markdown(f"**Dashboard URL:** {result['data']['dashboard_url']}")
            st.info("Check your Streamlit app sidebar for the new dashboard page!")
            st.rerun()
        else:
            st.error(f"Failed to create sample dashboard: {result['error']}")
    
    @staticmethod
    def _render_dashboard_stats(dashboard_manager: DashboardManager):
        """
        Render dashboard statistics.
        
        Args:
            dashboard_manager: Dashboard manager instance
        """
        stats = dashboard_manager.get_dashboard_stats()
        
        st.markdown("---")
        with st.expander("📊 Dashboard Statistics", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Dashboards", stats["total_dashboards"])
            with col2:
                st.metric("Total Charts", stats["total_charts"])
            with col3:
                chart_types = stats["chart_types"]
                most_common = max(chart_types.items(), key=lambda x: x[1])[0] if chart_types else "None"
                st.metric("Most Used Chart", most_common.title())
            
            if stats["chart_types"]:
                st.write("**Chart Types Distribution:**")
                for chart_type, count in stats["chart_types"].items():
                    st.write(f"- {chart_type.title()}: {count}")
    
    @staticmethod
    def render_help_section():
        """Render help and information section."""
        with st.expander("ℹ️ Help & Information", expanded=False):
            st.markdown("""
            **Dashboard Management (Streamlit Pages System):**
            - Each dashboard is created as a Streamlit page in the `pages/` folder
            - Dashboards automatically appear in your Streamlit app sidebar
            - Access dashboards directly via URLs
            - Pages are self-contained with API client and chart rendering
            
            **File Structure:**
            - `pages/dashboard_[title]_[timestamp].py` - Individual dashboard pages
            - `dashboards/dashboard_registry.json` - Registry of all created dashboards
            
            **Features:**
            - Native Streamlit pages (auto-navigation)
            - Direct URL access 
            - Built-in API client and chart rendering
            - Dark theme optimized
            - Auto-refresh capabilities
            - Interactive Plotly charts
            
            **Legacy Support:**
            - Old standalone Python files are still supported
            - Mixed format registry (pages + files)
            """)
            
            st.markdown("**Navigation Methods:**")
            st.markdown("1. **Sidebar:** Streamlit auto-detects pages in the `pages/` folder")
            st.markdown("2. **Direct URL:** Access via the deployed app URL")
            st.markdown("3. **Registry:** Click dashboard URLs from this page")
