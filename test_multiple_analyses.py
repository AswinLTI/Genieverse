#!/usr/bin/env python3
"""
Test multiple stock analysis storage
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock streamlit session state
import types
st_mock = types.ModuleType('streamlit')
st_mock.session_state = {}
sys.modules['streamlit'] = st_mock

from datetime import datetime

def test_multiple_analyses():
    """Test storing multiple stock analyses"""
    print("🧪 Testing Multiple Stock Analysis Storage...")
    
    # Simulate adding multiple analyses
    if 'stock_analyses' not in st_mock.session_state:
        st_mock.session_state['stock_analyses'] = []
    
    # Test data
    stocks = [
        {'symbol': 'TCS', 'time_period': '6M'},
        {'symbol': 'WIPRO', 'time_period': '6M'},
        {'symbol': 'RELIANCE', 'time_period': '3M'}
    ]
    
    for stock in stocks:
        # Check if analysis already exists and remove it
        st_mock.session_state['stock_analyses'] = [
            analysis for analysis in st_mock.session_state['stock_analyses'] 
            if not (analysis['symbol'] == stock['symbol'] and analysis['time_period'] == stock['time_period'])
        ]
        
        # Add new analysis
        analysis_data = {
            'symbol': stock['symbol'],
            'time_period': stock['time_period'],
            'data': f"mock_data_{stock['symbol']}",
            'timestamp': datetime.now(),
            'data_source': 'Sample'
        }
        st_mock.session_state['stock_analyses'].append(analysis_data)
        
        print(f"✅ Added analysis for {stock['symbol']} ({stock['time_period']})")
    
    print(f"\n📊 Total analyses stored: {len(st_mock.session_state['stock_analyses'])}")
    
    for i, analysis in enumerate(st_mock.session_state['stock_analyses'], 1):
        print(f"  {i}. {analysis['symbol']} ({analysis['time_period']}) - {analysis['data_source']}")
    
    print("\n🎯 Expected behavior:")
    print("• Each stock analysis is stored separately")
    print("• All analyses persist and display together")
    print("• New analysis for same stock replaces old one")
    print("• Clear All button removes everything")

if __name__ == "__main__":
    test_multiple_analyses()
