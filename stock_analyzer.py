#!/usr/bin/env python3
"""
Stock Analysis Module for Genieverse
Provides comprehensive stock analysis with interactive visualizations
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)

class StockAnalyzer:
    """
    Comprehensive stock analysis with interactive charts and insights
    """
    
    def __init__(self):
        """Initialize the stock analyzer"""
        self.analysis_types = {
            'price_trend': 'Price Trend Analysis',
            'volatility': 'Volatility Analysis', 
            'volume_analysis': 'Volume Analysis',
            'correlation': 'Price Correlation Analysis',
            'performance': 'Performance Metrics',
            'technical': 'Technical Indicators'
        }
        
    def detect_analysis_request(self, user_message: str) -> Optional[Dict[str, Any]]:
        """
        Detect if user is requesting stock analysis
        
        Args:
            user_message: User's chat message
            
        Returns:
            Analysis configuration dict or None
        """
        message_lower = user_message.lower()
        
        # Keywords that indicate analysis request
        analysis_keywords = [
            'analyze', 'analysis', 'analyse', 'performance', 'trend', 'volatility',
            'correlation', 'metrics', 'insights', 'study', 'examine', 'review'
        ]
        
        # Stock-related keywords
        stock_keywords = [
            'stock', 'share', 'equity', 'price', 'trading', 'market'
        ]
        
        # Check if message contains analysis request
        has_analysis = any(keyword in message_lower for keyword in analysis_keywords)
        has_stock = any(keyword in message_lower for keyword in stock_keywords)
        
        if has_analysis and has_stock:
            # Extract stock symbol and time period
            stock_symbol = self._extract_stock_symbol(user_message)
            time_period = self._extract_time_period(user_message)
            analysis_type = self._extract_analysis_type(user_message)
            
            return {
                'stock_symbol': stock_symbol,
                'time_period': time_period,
                'analysis_type': analysis_type,
                'is_analysis_request': True,
                'original_message': user_message
            }
        
        return None
    
    def _extract_stock_symbol(self, message: str) -> str:
        """Extract stock symbol from message"""
        message_upper = message.upper()
        
        # Common stock symbols with variations
        stock_symbols = {
            'TCS': ['TCS', 'TATA CONSULTANCY', 'TATA CONSULTANCY SERVICES'],
            'INFY': ['INFY', 'INFOSYS'],
            'WIPRO': ['WIPRO'],
            'RELIANCE': ['RELIANCE', 'RIL'],
            'HDFCBANK': ['HDFC', 'HDFCBANK', 'HDFC BANK'],
            'ICICIBANK': ['ICICI', 'ICICIBANK', 'ICICI BANK'],
            'SBI': ['SBI', 'STATE BANK'],
            'ITC': ['ITC'],
            'BHARTIARTL': ['BHARTI', 'BHARTIARTL', 'AIRTEL'],
            'KOTAKBANK': ['KOTAK', 'KOTAKBANK', 'KOTAK BANK'],
            'BAJAJ': ['BAJAJ'],
            'MARUTI': ['MARUTI'],
            'LT': ['LT', 'L&T', 'LARSEN'],
            'ONGC': ['ONGC'],
            'NTPC': ['NTPC'],
            'POWERGRID': ['POWERGRID', 'POWER GRID'],
            'COALINDIA': ['COALINDIA', 'COAL INDIA'],
            'HINDALCO': ['HINDALCO'],
            'JSWSTEEL': ['JSW', 'JSWSTEEL', 'JSW STEEL'],
            'TATASTEEL': ['TATA STEEL', 'TATASTEEL']
        }
        
        # Check for exact matches first
        for symbol, variations in stock_symbols.items():
            for variation in variations:
                if variation in message_upper:
                    return symbol
        
        # Check for pattern-based matches
        stock_patterns = [
            r'\b([A-Z]{2,6})\s+(?:stock|share|equity)\b',
            r'\b(?:stock|share|equity)\s+([A-Z]{2,6})\b',
            r'\b([A-Z]{3,6})\b'  # Generic 3-6 letter symbols
        ]
        
        for pattern in stock_patterns:
            match = re.search(pattern, message_upper)
            if match:
                potential_symbol = match.group(1)
                # Only return if it's a known symbol or looks like a stock symbol
                if potential_symbol in stock_symbols or len(potential_symbol) >= 3:
                    return potential_symbol
        
        # Default to TCS if no specific stock mentioned
        return 'TCS'
    
    def _extract_time_period(self, message: str) -> str:
        """Extract time period from message"""
        message_lower = message.lower()
        
        if any(term in message_lower for term in ['6 month', '6-month', 'six month', 'half year']):
            return '6M'
        elif any(term in message_lower for term in ['3 month', '3-month', 'three month', 'quarter']):
            return '3M'
        elif any(term in message_lower for term in ['1 year', 'yearly', 'annual']):
            return '1Y'
        elif any(term in message_lower for term in ['1 month', 'monthly']):
            return '1M'
        
        # Default to 6 months
        return '6M'
    
    def _extract_analysis_type(self, message: str) -> str:
        """Extract specific analysis type from message"""
        message_lower = message.lower()
        
        if any(term in message_lower for term in ['volatility', 'volatile', 'risk']):
            return 'volatility'
        elif any(term in message_lower for term in ['volume', 'trading volume']):
            return 'volume_analysis'
        elif any(term in message_lower for term in ['correlation', 'relationship']):
            return 'correlation'
        elif any(term in message_lower for term in ['performance', 'returns', 'growth']):
            return 'performance'
        elif any(term in message_lower for term in ['technical', 'indicators', 'moving average']):
            return 'technical'
        
        # Default to comprehensive price trend analysis
        return 'price_trend'
    
    def generate_analysis_data(self, stock_symbol: str, time_period: str) -> pd.DataFrame:
        """
        Fetch real stock data from API and database
        
        Args:
            stock_symbol: Stock symbol (e.g., 'TCS', 'WIPRO')
            time_period: Time period ('1M', '3M', '6M', '1Y')
            
        Returns:
            DataFrame with stock data from API/database
        """
        import streamlit as st
        
        # Check if API client is available
        if not st.session_state.get("api_client"):
            logger.warning("API client not available, falling back to sample data")
            return self._generate_sample_data(stock_symbol, time_period)
        
        api_client = st.session_state["api_client"]
        
        # Map time periods to database-friendly formats for last available data
        period_map = {
            '1M': 'last available 1 month',
            '3M': 'last available 3 months', 
            '6M': 'last available 6 months',
            '1Y': 'last available 1 year'
        }
        
        period_text = period_map.get(time_period, 'last available 6 months')
        
        # Construct API query for stock data - get last available data from dataset
        api_query = f"Get the stock price data for {stock_symbol} stock for the {period_text} of data available in the dataset including open, high, low, close prices and volume in JSON format with columns Date, Open, High, Low, Close, Volume"
        
        try:
            logger.info(f"Fetching real stock data for {stock_symbol} ({time_period}) via API")
            
            # Make API call to get stock data
            result = api_client.send_query(api_query)
            
            if not result["success"]:
                # Try alternative query format if first one fails
                alt_query = f"Show me the most recent {period_text.replace('last available ', '')} of {stock_symbol} stock data with Date, Open, High, Low, Close, Volume columns in JSON format"
                logger.info(f"Trying alternative query format: {alt_query}")
                result = api_client.send_query(alt_query)
                
                if not result["success"]:
                    # Try third query format - very simple
                    simple_query = f"Get {stock_symbol} stock price data with Date, Open, High, Low, Close, Volume"
                    logger.info(f"Trying simple query format: {simple_query}")
                    result = api_client.send_query(simple_query)
            
            if result["success"]:
                api_response = result["data"]
                
                # Extract chart data using existing processor
                from main_app import extract_chart_data
                chart_data = extract_chart_data(api_response)
                
                if chart_data and "json_generator_data" in chart_data:
                    json_data = chart_data["json_generator_data"]
                    
                    if "data" in json_data and json_data["data"]:
                        # Convert API data to DataFrame
                        df = pd.DataFrame(json_data["data"])
                        
                        # Ensure required columns exist
                        required_cols = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
                        missing_cols = [col for col in required_cols if col not in df.columns]
                        
                        if not missing_cols:
                            # Clean and format data
                            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                            
                            # Convert price columns to numeric
                            for col in ['Open', 'High', 'Low', 'Close']:
                                df[col] = pd.to_numeric(df[col], errors='coerce')
                            
                            df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
                            
                            # Remove any rows with invalid data
                            df = df.dropna()
                            
                            if len(df) > 0:
                                logger.info(f"Successfully fetched {len(df)} records for {stock_symbol}")
                                # Mark as API data
                                df.attrs['api_fetched'] = True
                                return df.sort_values('Date').reset_index(drop=True)
                            else:
                                logger.warning("No valid data after cleaning, using sample data")
                        else:
                            logger.warning(f"Missing required columns {missing_cols}, using sample data")
                    else:
                        logger.warning("No data in API response, using sample data")
                else:
                    logger.warning("No chart data in API response, using sample data")
            else:
                logger.warning(f"API request failed: {result.get('error', 'Unknown error')}, using sample data")
                
        except Exception as e:
            logger.error(f"Error fetching stock data from API: {e}, using sample data")
        
        # Fallback to sample data if API fails
        logger.info(f"Falling back to sample data for {stock_symbol}")
        return self._generate_sample_data(stock_symbol, time_period)
    
    def _generate_sample_data(self, stock_symbol: str, time_period: str) -> pd.DataFrame:
        """
        Generate sample stock data as fallback when API is unavailable
        
        Args:
            stock_symbol: Stock symbol (e.g., 'TCS', 'WIPRO')
            time_period: Time period ('1M', '3M', '6M', '1Y')
            
        Returns:
            DataFrame with sample stock data
        """
        # Determine number of days based on period
        days_map = {'1M': 30, '3M': 90, '6M': 180, '1Y': 365}
        days = days_map.get(time_period, 180)
        
        # Stock-specific configurations (realistic base prices)
        stock_configs = {
            'TCS': {'base_price': 3400, 'volatility': 0.018},
            'INFY': {'base_price': 1450, 'volatility': 0.022},
            'WIPRO': {'base_price': 420, 'volatility': 0.025},
            'RELIANCE': {'base_price': 2300, 'volatility': 0.020},
            'HDFCBANK': {'base_price': 1550, 'volatility': 0.016},
            'ICICIBANK': {'base_price': 950, 'volatility': 0.019},
            'SBI': {'base_price': 580, 'volatility': 0.024},
            'ITC': {'base_price': 420, 'volatility': 0.017},
            'BHARTIARTL': {'base_price': 850, 'volatility': 0.021},
            'KOTAKBANK': {'base_price': 1720, 'volatility': 0.018}
        }
        
        config = stock_configs.get(stock_symbol, {'base_price': 2000, 'volatility': 0.020})
        
        # Generate dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Filter out weekends
        dates = [date for date in dates if date.weekday() < 5]
        
        # Generate stock-specific seed
        stock_seed = hash(stock_symbol) % 10000
        np.random.seed(stock_seed)
        
        data = []
        current_price = config['base_price']
        
        for i, date in enumerate(dates):
            # Realistic stock movement (smaller daily changes)
            daily_trend = np.random.normal(0.0002, config['volatility'] / 50)  # Much smaller daily changes
            volatility = np.random.normal(0, config['volatility'] / 20)
            
            daily_change = daily_trend + volatility
            open_price = current_price
            
            # More realistic intraday spreads
            high_spread = abs(np.random.normal(0.005, 0.002))
            low_spread = abs(np.random.normal(0.004, 0.002))
            
            high_price = open_price * (1 + high_spread)
            low_price = open_price * (1 - low_spread)
            close_price = open_price * (1 + daily_change)
            
            # Ensure logical OHLC relationship
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            # Realistic volume
            base_volume = 1000000 + (hash(stock_symbol) % 500000)
            volume = int(base_volume * np.random.uniform(0.7, 1.3))
            
            data.append({
                'Date': date,
                'Open': round(open_price, 2),
                'High': round(high_price, 2),
                'Low': round(low_price, 2),
                'Close': round(close_price, 2),
                'Volume': volume
            })
            
            current_price = close_price
        
        return pd.DataFrame(data)
    
    def create_comprehensive_analysis(self, analysis_config: Dict[str, Any]) -> None:
        """
        Create comprehensive stock analysis based on configuration
        
        Args:
            analysis_config: Analysis configuration from detect_analysis_request
        """
        stock_symbol = analysis_config['stock_symbol']
        time_period = analysis_config['time_period']
        analysis_type = analysis_config['analysis_type']
        
        st.markdown(f"## 📊 {stock_symbol} Stock Analysis ({time_period})")
        st.markdown(f"**Analysis Type**: {self.analysis_types.get(analysis_type, 'Comprehensive Analysis')}")
        
        # Generate data
        with st.spinner(f"Analyzing {stock_symbol} stock data for the last {time_period}..."):
            df = self.generate_analysis_data(stock_symbol, time_period)
        
        if df.empty:
            st.error("No data available for analysis")
            return
        
        # Convert Date to datetime for better handling
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Create tabs for different analysis views
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Price Analysis", 
            "📊 Performance Metrics", 
            "🔍 Detailed Charts", 
            "📋 Data & Insights"
        ])
        
        with tab1:
            self._create_price_analysis(df, stock_symbol, time_period)
        
        with tab2:
            self._create_performance_metrics(df, stock_symbol, time_period)
        
        with tab3:
            self._create_detailed_charts(df, stock_symbol, analysis_type)
        
        with tab4:
            self._create_data_insights(df, stock_symbol, time_period)
    
    def _create_price_analysis(self, df: pd.DataFrame, stock_symbol: str, time_period: str) -> None:
        """Create price trend analysis"""
        
        # Main price chart
        fig = go.Figure()
        
        # Candlestick chart
        fig.add_trace(go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name=f'{stock_symbol} Price',
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444'
        ))
        
        # Add moving averages
        df['MA_20'] = df['Close'].rolling(window=20).mean()
        df['MA_50'] = df['Close'].rolling(window=50).mean()
        
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['MA_20'],
            name='20-Day MA',
            line=dict(color='orange', width=2),
            opacity=0.7
        ))
        
        if len(df) > 50:
            fig.add_trace(go.Scatter(
                x=df['Date'],
                y=df['MA_50'],
                name='50-Day MA',
                line=dict(color='purple', width=2),
                opacity=0.7
            ))
        
        fig.update_layout(
            title=f'{stock_symbol} Price Trend Analysis ({time_period})',
            xaxis_title='Date',
            yaxis_title='Price (₹)',
            template='plotly_dark',
            height=600,
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Price summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        current_price = df['Close'].iloc[-1]
        start_price = df['Close'].iloc[0]
        price_change = current_price - start_price
        price_change_pct = (price_change / start_price) * 100
        
        with col1:
            st.metric("Current Price", f"₹{current_price:.2f}")
        with col2:
            st.metric("Period Change", f"₹{price_change:.2f}", f"{price_change_pct:.2f}%")
        with col3:
            st.metric("Highest", f"₹{df['High'].max():.2f}")
        with col4:
            st.metric("Lowest", f"₹{df['Low'].min():.2f}")
    
    def _create_performance_metrics(self, df: pd.DataFrame, stock_symbol: str, time_period: str) -> None:
        """Create performance metrics analysis"""
        
        # Calculate returns
        df['Daily_Return'] = df['Close'].pct_change()
        df['Cumulative_Return'] = (1 + df['Daily_Return']).cumprod() - 1
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Returns distribution
            fig_dist = px.histogram(
                df, 
                x='Daily_Return',
                title='Daily Returns Distribution',
                template='plotly_dark',
                nbins=30
            )
            fig_dist.update_layout(height=400)
            st.plotly_chart(fig_dist, use_container_width=True)
        
        with col2:
            # Cumulative returns
            fig_cum = go.Figure()
            fig_cum.add_trace(go.Scatter(
                x=df['Date'],
                y=df['Cumulative_Return'] * 100,
                mode='lines',
                name='Cumulative Return',
                line=dict(color='#00ff88', width=3)
            ))
            
            fig_cum.update_layout(
                title='Cumulative Returns Over Time',
                xaxis_title='Date',
                yaxis_title='Cumulative Return (%)',
                template='plotly_dark',
                height=400
            )
            st.plotly_chart(fig_cum, use_container_width=True)
        
        # Performance metrics
        st.markdown("### 📈 Key Performance Metrics")
        
        # Calculate metrics
        total_return = df['Cumulative_Return'].iloc[-1] * 100
        volatility = df['Daily_Return'].std() * np.sqrt(252) * 100  # Annualized
        sharpe_ratio = (df['Daily_Return'].mean() / df['Daily_Return'].std()) * np.sqrt(252)
        max_drawdown = ((df['Close'] / df['Close'].cummax()) - 1).min() * 100
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Return", f"{total_return:.2f}%")
        with col2:
            st.metric("Volatility (Annual)", f"{volatility:.2f}%")
        with col3:
            st.metric("Sharpe Ratio", f"{sharpe_ratio:.2f}")
        with col4:
            st.metric("Max Drawdown", f"{max_drawdown:.2f}%")
    
    def _create_detailed_charts(self, df: pd.DataFrame, stock_symbol: str, analysis_type: str) -> None:
        """Create detailed analysis charts based on type"""
        
        if analysis_type == 'volume_analysis':
            # Volume analysis
            fig_vol = go.Figure()
            
            # Volume bars
            colors = ['red' if close < open else 'green' 
                     for close, open in zip(df['Close'], df['Open'])]
            
            fig_vol.add_trace(go.Bar(
                x=df['Date'],
                y=df['Volume'],
                marker_color=colors,
                name='Volume',
                opacity=0.7
            ))
            
            fig_vol.update_layout(
                title=f'{stock_symbol} Trading Volume Analysis',
                xaxis_title='Date',
                yaxis_title='Volume',
                template='plotly_dark',
                height=500
            )
            
            st.plotly_chart(fig_vol, use_container_width=True)
            
        elif analysis_type == 'volatility':
            # Volatility analysis
            df['Volatility'] = df['Daily_Return'].rolling(window=20).std() * np.sqrt(252) * 100
            
            fig_vol = go.Figure()
            fig_vol.add_trace(go.Scatter(
                x=df['Date'],
                y=df['Volatility'],
                mode='lines',
                name='20-Day Volatility',
                line=dict(color='orange', width=2)
            ))
            
            fig_vol.update_layout(
                title=f'{stock_symbol} Volatility Analysis',
                xaxis_title='Date',
                yaxis_title='Volatility (%)',
                template='plotly_dark',
                height=500
            )
            
            st.plotly_chart(fig_vol, use_container_width=True)
        
        elif analysis_type == 'correlation':
            # Price correlation analysis (Open vs Close)
            fig_corr = go.Figure()
            
            fig_corr.add_trace(go.Scatter(
                x=df['Open'],
                y=df['Close'],
                mode='markers',
                marker=dict(
                    size=8,
                    color=df.index,
                    colorscale='Viridis',
                    colorbar=dict(title="Time Sequence")
                ),
                text=df['Date'].dt.strftime('%Y-%m-%d'),
                hovertemplate='<b>%{text}</b><br>Open: ₹%{x:.2f}<br>Close: ₹%{y:.2f}<extra></extra>',
                name='Open vs Close'
            ))
            
            # Add diagonal line
            min_price = min(df['Open'].min(), df['Close'].min())
            max_price = max(df['Open'].max(), df['Close'].max())
            
            fig_corr.add_trace(go.Scatter(
                x=[min_price, max_price],
                y=[min_price, max_price],
                mode='lines',
                line=dict(dash='dash', color='red', width=2),
                name='Break-even Line'
            ))
            
            correlation = df['Open'].corr(df['Close'])
            
            fig_corr.update_layout(
                title=f'{stock_symbol} Open vs Close Price Correlation (r={correlation:.3f})',
                xaxis_title='Opening Price (₹)',
                yaxis_title='Closing Price (₹)',
                template='plotly_dark',
                height=500
            )
            
            st.plotly_chart(fig_corr, use_container_width=True)
        
        else:
            # Default: Technical indicators
            df['RSI'] = self._calculate_rsi(df['Close'])
            df['MACD'], df['MACD_Signal'] = self._calculate_macd(df['Close'])
            
            # RSI Chart
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(
                x=df['Date'],
                y=df['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=2)
            ))
            
            # Add RSI levels
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought (70)")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold (30)")
            
            fig_rsi.update_layout(
                title=f'{stock_symbol} RSI (Relative Strength Index)',
                xaxis_title='Date',
                yaxis_title='RSI',
                template='plotly_dark',
                height=400
            )
            
            st.plotly_chart(fig_rsi, use_container_width=True)
    
    def _create_data_insights(self, df: pd.DataFrame, stock_symbol: str, time_period: str) -> None:
        """Create data table and insights"""
        
        # Key insights
        st.markdown("### 🔍 Key Insights")
        
        # Calculate insights
        avg_volume = df['Volume'].mean()
        price_volatility = df['Daily_Return'].std() * 100
        best_day = df.loc[df['Daily_Return'].idxmax()]
        worst_day = df.loc[df['Daily_Return'].idxmin()]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📈 Performance Highlights:**")
            st.write(f"• Average daily volume: {avg_volume:,.0f}")
            st.write(f"• Daily volatility: {price_volatility:.2f}%")
            st.write(f"• Best trading day: {best_day['Date'].strftime('%Y-%m-%d')} (+{best_day['Daily_Return']*100:.2f}%)")
            st.write(f"• Worst trading day: {worst_day['Date'].strftime('%Y-%m-%d')} ({worst_day['Daily_Return']*100:.2f}%)")
        
        with col2:
            st.markdown("**🎯 Trading Recommendations:**")
            current_rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else 50
            
            if current_rsi > 70:
                st.warning("🔴 RSI indicates overbought condition - Consider taking profits")
            elif current_rsi < 30:
                st.success("🟢 RSI indicates oversold condition - Potential buying opportunity")
            else:
                st.info("🟡 RSI in neutral zone - Monitor for breakout signals")
            
            if df['Close'].iloc[-1] > df['MA_20'].iloc[-1]:
                st.success("📈 Price above 20-day moving average - Bullish trend")
            else:
                st.warning("📉 Price below 20-day moving average - Bearish trend")
        
        # Data table
        if st.checkbox("📊 Show Raw Data"):
            st.markdown("### 📋 Stock Data")
            display_df = df[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']].copy()
            display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(
                display_df.style.format({
                    'Open': '₹{:.2f}',
                    'High': '₹{:.2f}',
                    'Low': '₹{:.2f}',
                    'Close': '₹{:.2f}',
                    'Volume': '{:,.0f}'
                }),
                use_container_width=True
            )
    
    def _calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
        """Calculate MACD indicator"""
        exp1 = prices.ewm(span=fast).mean()
        exp2 = prices.ewm(span=slow).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal).mean()
        return macd, signal_line
    
    def _create_candlestick_chart(self, data: pd.DataFrame, symbol: str) -> go.Figure:
        """Create candlestick chart"""
        fig = go.Figure(data=go.Candlestick(
            x=data['Date'],
            open=data['Open'],
            high=data['High'], 
            low=data['Low'],
            close=data['Close'],
            name=f"{symbol} Candlestick"
        ))
        
        fig.update_layout(
            title=f"{symbol} Candlestick Chart",
            xaxis_title="Date",
            yaxis_title="Price",
            height=500
        )
        
        return fig
    
    def _create_price_chart(self, data: pd.DataFrame, symbol: str) -> go.Figure:
        """Create price trend chart"""
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=data['Date'],
            y=data['Close'],
            mode='lines',
            name='Close Price',
            line=dict(color='blue', width=2)
        ))
        
        # Add moving averages
        if len(data) >= 20:
            data['MA20'] = data['Close'].rolling(20).mean()
            fig.add_trace(go.Scatter(
                x=data['Date'],
                y=data['MA20'],
                mode='lines',
                name='20-day MA',
                line=dict(color='orange', width=1)
            ))
        
        if len(data) >= 50:
            data['MA50'] = data['Close'].rolling(50).mean()
            fig.add_trace(go.Scatter(
                x=data['Date'],
                y=data['MA50'], 
                mode='lines',
                name='50-day MA',
                line=dict(color='red', width=1)
            ))
        
        fig.update_layout(
            title=f"{symbol} Price Trend",
            xaxis_title="Date",
            yaxis_title="Price",
            height=400
        )
        
        return fig
    
    def _create_technical_chart(self, data: pd.DataFrame, symbol: str) -> go.Figure:
        """Create technical indicators chart"""
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=['RSI', 'MACD'],
            vertical_spacing=0.1
        )
        
        # Calculate RSI
        if len(data) >= 14:
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            fig.add_trace(go.Scatter(
                x=data['Date'],
                y=rsi,
                mode='lines',
                name='RSI',
                line=dict(color='purple')
            ), row=1, col=1)
            
            # RSI reference lines
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=1, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=1, col=1)
        
        # Calculate MACD
        if len(data) >= 26:
            ema12 = data['Close'].ewm(span=12).mean()
            ema26 = data['Close'].ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            histogram = macd - signal
            
            fig.add_trace(go.Scatter(
                x=data['Date'],
                y=macd,
                mode='lines',
                name='MACD',
                line=dict(color='blue')
            ), row=2, col=1)
            
            fig.add_trace(go.Scatter(
                x=data['Date'],
                y=signal,
                mode='lines',
                name='Signal',
                line=dict(color='red')
            ), row=2, col=1)
        
        fig.update_layout(
            title=f"{symbol} Technical Indicators",
            height=500
        )
        
        return fig
    
    def _create_volume_chart(self, data: pd.DataFrame, symbol: str) -> go.Figure:
        """Create volume analysis chart"""
        fig = go.Figure()
        
        # Volume bars
        colors = ['red' if close < open else 'green' 
                 for close, open in zip(data['Close'], data['Open'])]
        
        fig.add_trace(go.Bar(
            x=data['Date'],
            y=data['Volume'],
            marker_color=colors,
            name='Volume',
            opacity=0.7
        ))
        
        # Volume moving average
        if len(data) >= 20:
            volume_ma = data['Volume'].rolling(20).mean()
            fig.add_trace(go.Scatter(
                x=data['Date'],
                y=volume_ma,
                mode='lines',
                name='Volume MA20',
                line=dict(color='orange', width=2)
            ))
        
        fig.update_layout(
            title=f"{symbol} Volume Analysis",
            xaxis_title="Date",
            yaxis_title="Volume",
            height=400
        )
        
        return fig
    
    def _calculate_performance_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        """Calculate performance metrics"""
        if len(data) < 2:
            return {}
        
        # Calculate returns
        returns = data['Close'].pct_change().dropna()
        
        # Total return
        total_return = ((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100
        
        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252) * 100
        
        # Max drawdown
        peak = data['Close'].expanding().max()
        drawdown = (data['Close'] - peak) / peak * 100
        max_drawdown = drawdown.min()
        
        # Sharpe ratio (assuming 0% risk-free rate)
        sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        return {
            'total_return': total_return,
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio
        }
    
    def _create_returns_chart(self, data: pd.DataFrame, symbol: str) -> go.Figure:
        """Create returns analysis chart"""
        returns = data['Close'].pct_change().dropna()
        cumulative_returns = (1 + returns).cumprod() - 1
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=['Cumulative Returns', 'Daily Returns Distribution'],
            vertical_spacing=0.1
        )
        
        # Cumulative returns
        fig.add_trace(go.Scatter(
            x=data['Date'][1:],
            y=cumulative_returns * 100,
            mode='lines',
            name='Cumulative Returns (%)',
            line=dict(color='green')
        ), row=1, col=1)
        
        # Returns histogram
        fig.add_trace(go.Histogram(
            x=returns * 100,
            nbinsx=30,
            name='Daily Returns (%)',
            marker_color='lightblue'
        ), row=2, col=1)
        
        fig.update_layout(
            title=f"{symbol} Returns Analysis",
            height=500
        )
        
        return fig
    
    def _generate_insights(self, data: pd.DataFrame, metrics: Dict[str, float], symbol: str) -> List[str]:
        """Generate trading insights"""
        insights = []
        
        if not metrics:
            return ["📊 Insufficient data for detailed insights"]
        
        # Price trend analysis
        recent_change = ((data['Close'].iloc[-1] / data['Close'].iloc[-5]) - 1) * 100 if len(data) >= 5 else 0
        
        if recent_change > 5:
            insights.append(f"🟢 **Strong upward momentum**: {symbol} gained {recent_change:.1f}% in recent trading")
        elif recent_change < -5:
            insights.append(f"🔴 **Downward pressure**: {symbol} declined {abs(recent_change):.1f}% recently")
        else:
            insights.append(f"⚪ **Stable price action**: {symbol} showing modest {recent_change:.1f}% movement")
        
        # Volatility analysis
        volatility = metrics.get('volatility', 0)
        if volatility > 30:
            insights.append(f"⚡ **High volatility**: {volatility:.1f}% annualized volatility indicates elevated risk")
        elif volatility < 15:
            insights.append(f"📉 **Low volatility**: {volatility:.1f}% annualized volatility suggests stable price action")
        else:
            insights.append(f"📊 **Moderate volatility**: {volatility:.1f}% annualized volatility within normal range")
        
        # Performance analysis
        total_return = metrics.get('total_return', 0)
        if total_return > 20:
            insights.append(f"🚀 **Strong performance**: {total_return:.1f}% total return demonstrates excellent growth")
        elif total_return < -10:
            insights.append(f"📉 **Underperformance**: {total_return:.1f}% total return indicates challenges")
        else:
            insights.append(f"📈 **Moderate performance**: {total_return:.1f}% total return shows steady progress")
        
        # Risk assessment
        max_drawdown = metrics.get('max_drawdown', 0)
        if max_drawdown < -20:
            insights.append(f"⚠️ **High risk**: {abs(max_drawdown):.1f}% maximum drawdown suggests significant downside risk")
        elif max_drawdown > -5:
            insights.append(f"✅ **Low risk**: {abs(max_drawdown):.1f}% maximum drawdown indicates controlled risk")
        else:
            insights.append(f"🔶 **Moderate risk**: {abs(max_drawdown):.1f}% maximum drawdown shows acceptable risk levels")
        
        return insights
