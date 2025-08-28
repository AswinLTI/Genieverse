# API Routing Documentation

## Intelligent Query Routing

The application now includes intelligent routing to automatically direct queries to the appropriate API based on content analysis.

### Routing Logic

#### Main Blueverse API (Simple Queries)
**Endpoint**: `Genieverse_9b5befb3` / `68ac66333c336dbd12b96e10`

Used for:
- General questions and explanations
- Conceptual queries about data analysis
- Simple informational requests
- Best practices and recommendations

**Example queries**:
- "What is Databricks?"
- "How do I connect to a database?"
- "Explain data warehousing concepts"
- "What are best practices for data analysis?"

#### JSON Generator API (Charts & Tables)
**Endpoint**: `Json_Generator_975a2dc0` / `68ae94113d219c7a19e1446d`

Used for:
- Chart and visualization requests
- Raw data display and tables
- SQL queries and data retrieval
- Data analysis with visual output

**Chart Keywords**:
- chart, plot, graph, visualize, visualization
- bar chart, line chart, pie chart, scatter plot
- histogram, heatmap, candlestick, stacked bar
- create chart, show chart, generate chart, plot data

**Table/Data Keywords**:
- table, raw data, show data, view data, display data
- data table, show table, preview data, sample data
- first rows, head, limit, select, query, sql
- dataframe, dataset

### Automatic Classification

The system automatically analyzes each query and routes it to the appropriate API:

1. **Keyword Analysis**: Scans for chart, table, and data-related terms
2. **Intent Detection**: Determines if the user wants visualization or raw data
3. **Smart Routing**: Sends query to the most appropriate API
4. **Response Processing**: Handles responses from both APIs uniformly

### Visual Indicators

Users will see routing information in responses:
- 🔹 *Routed to Main API (Simple Query)*
- 📊 *Routed to JSON Generator API (Chart/Table Query)*

### Manual Override

If the automatic routing doesn't work as expected, users can:
1. Be more specific in their queries
2. Use explicit keywords like "create a chart" or "show me data"
3. Rephrase the question to include routing keywords

### Testing

Use the test script to verify routing:
```bash
python test_api.py
```

This will test both APIs with appropriate query types and show routing behavior.
