# Blueverse Foundry API-Based Application

This application provides a Streamlit UI that connects to the Blueverse Foundry platform via REST API calls instead of using LangChain agents.

## 🚀 Features

- **API-Based Communication**: Direct REST API calls to Blueverse Foundry
- **Interactive Chat Interface**: Same UI experience as the original agent-based app
- **Chart Visualization**: Automatic detection and display of charts from API responses
- **Real-time Communication**: Direct connection to your Blueverse Foundry workspace
- **Configuration Management**: Easy token management via environment variables or UI

## 📋 Prerequisites

1. **Blueverse Foundry Access**: Active workspace with API access
2. **API Token**: Valid authentication token for the Blueverse Foundry service
3. **Python Environment**: Python 3.8+ with required packages

## 🛠️ Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements_api.txt
```

### 2. Configure API Token

#### Option A: Environment File (Recommended)
```bash
# Copy the template
cp .env.template .env

# Edit .env file and add your token
BLUEVERSE_API_TOKEN=your_actual_api_token_here
```

#### Option B: Set via UI
- Run the application
- Use the sidebar to enter your API token
- Token will be used for the current session

### 3. Test API Connection

Before running the full application, test your API connection:

```bash
python test_api.py
```

This will:
- Verify your API token is configured
- Test the connection to Blueverse Foundry
- Show example API responses
- Help troubleshoot any connectivity issues

### 4. Run the Application

```bash
streamlit run api_app.py
```

## 🔧 Configuration

### API Endpoint Settings

The application is pre-configured with:
- **URL**: `https://blueverse-foundry.ltimindtree.com/chatservice/chat`
- **Space Name**: `Genieverse_9b5befb3`
- **Flow ID**: `68ac66333c336dbd12b96e10`

To modify these settings, edit the constants in `api_app.py`:

```python
API_BASE_URL = "your_api_endpoint"
SPACE_NAME = "your_space_name"
FLOW_ID = "your_flow_id"
```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `BLUEVERSE_API_TOKEN` | Your Blueverse Foundry API token | Yes |
| `OPEN_API_KEY` | OpenAI API key (fallback) | No |
| `DATABRICKS_HOST` | Databricks host (direct access) | No |
| `DATABRICKS_TOKEN` | Databricks token (direct access) | No |

## 🎯 Usage

### Basic Queries

The application supports the same types of queries as the original agent:

```text
# Data queries
"Show me the available tables"
"Query the customers table and show first 10 rows"
"SELECT * FROM sales WHERE region = 'North' LIMIT 5"

# Visualizations
"Create a bar chart showing sales by region"
"Plot a line chart of stock prices over time"
"Show me a pie chart of customer distribution"

# Analysis
"What data is currently available?"
"Analyze the trend in quarterly sales"
"Forecast next quarter's revenue"
```

### Chart Support

The application automatically detects and displays charts returned by the API. Supported formats:
- **Plotly JSON**: Automatically rendered as interactive charts
- **Chart Data**: Converted to Plotly figures for display
- **Error Handling**: Graceful fallback for unsupported chart formats

## 🔍 API Response Handling

The application intelligently processes API responses by:

1. **Extracting Text**: Looks for response text in common fields (`response`, `message`, `content`, etc.)
2. **Finding Charts**: Searches for chart data in various response structures
3. **Error Processing**: Handles API errors and connection issues gracefully
4. **Logging**: Provides detailed logs for debugging

## 🐛 Troubleshooting

### Common Issues

#### 1. "API client not configured"
- **Cause**: Missing or invalid API token
- **Solution**: Set `BLUEVERSE_API_TOKEN` in `.env` file or via sidebar

#### 2. "API Error 401: Unauthorized"
- **Cause**: Invalid API token
- **Solution**: Verify your token is correct and has proper permissions

#### 3. "Connection Error"
- **Cause**: Network connectivity or API endpoint issues
- **Solution**: Check internet connection and API endpoint availability

#### 4. Charts not displaying
- **Cause**: API response doesn't contain expected chart format
- **Solution**: Check API response structure and update chart extraction logic

### Debug Mode

Enable detailed logging by setting the log level:

```python
# In api_app.py, change the logging level
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
```

### Testing

Use the test script to verify your setup:

```bash
# Test basic connection
python test_api.py

# Test with specific queries
python test_api.py
# When prompted, choose 'y' to test example queries
```

## 📁 File Structure

```
tools bf/
├── api_app.py              # Main Streamlit application
├── test_api.py             # API connection test script
├── requirements_api.txt    # Python dependencies
├── .env.template          # Environment variables template
├── .env                   # Your actual environment variables (create this)
└── static/
    └── genie.png          # UI assets
```

## 🔄 Migration from Agent-based App

If you're migrating from the original LangChain agent application:

1. **Backup**: Save your current `.env` file
2. **Install**: Install new dependencies from `requirements_api.txt`
3. **Configure**: Add `BLUEVERSE_API_TOKEN` to your `.env` file
4. **Test**: Run `test_api.py` to verify connectivity
5. **Run**: Start the new app with `streamlit run api_app.py`

The UI and functionality remain identical - only the backend communication method changes.

## 🆘 Support

For additional support:
1. Check the troubleshooting section above
2. Run the test script to identify specific issues
3. Review the application logs for detailed error information
4. Verify your Blueverse Foundry workspace configuration

## ⚡ Performance Notes

- **Response Time**: API calls may take 5-30 seconds depending on query complexity
- **Chart Rendering**: Large datasets may take additional time to render
- **Concurrent Users**: Each user session maintains independent API connections
- **Rate Limiting**: Be aware of API rate limits in your Blueverse Foundry plan
