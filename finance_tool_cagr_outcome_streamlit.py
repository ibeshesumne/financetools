import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf

# App title
st.title('Equity Performance')

# Sidebar inputs
symbol_input = st.sidebar.text_input('Enter Stock Symbol', 'BE')
benchmark_input = st.sidebar.text_input('Enter Benchmark Symbol', '^IXIC')
start_date = st.sidebar.date_input('Start Date', value=pd.to_datetime('2010-01-01'))
end_date = st.sidebar.date_input('End Date', value=pd.to_datetime('2024-12-31'))

# Function to fetch data
def fetch_data(symbol, start_date, end_date):
    try:
        if not symbol or not symbol.strip():
            st.error("Symbol cannot be empty")
            return None
            
        data = yf.download(symbol.strip(), start=start_date, end=end_date)
        if data.empty:
            st.error(f"No data found for symbol: {symbol}")
            return None
        
        # Validate that we have enough data points
        if len(data) < 2:
            st.error(f"Insufficient data for symbol: {symbol}")
            return None
            
        return data
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

# Function to calculate CAGR and overall gain
def calculate_metrics(data):
    if data is None or data.empty:
        return None, None
    
    try:
        # Handle MultiIndex columns from yfinance
        if isinstance(data.columns, pd.MultiIndex):
            # Get the first (and likely only) symbol's data
            adj_close_col = data['Adj Close'].iloc[:, 0] if len(data['Adj Close'].columns) > 0 else data['Adj Close']
        else:
            adj_close_col = data['Adj Close']
        
        # Validate data
        if len(adj_close_col) < 2:
            st.error("Insufficient data for calculation")
            return None, None
            
        first_price = adj_close_col.iloc[0]
        last_price = adj_close_col.iloc[-1]
        
        # Check for valid prices
        if pd.isna(first_price) or pd.isna(last_price) or first_price <= 0:
            st.error("Invalid price data")
            return None, None
            
        days = (data.index[-1] - data.index[0]).days
        
        # Avoid division by zero
        if days <= 0:
            st.error("Invalid date range")
            return None, None
            
        cagr = ((last_price / first_price) ** (365.25 / days) - 1) * 100
        overall_gain = ((last_price - first_price) / first_price) * 100
        return round(cagr, 2), round(overall_gain, 2)
    except Exception as e:
        st.error(f"Error calculating metrics: {str(e)}")
        return None, None

# Function to calculate annual returns
def calculate_annual_returns(data):
    if data is None or data.empty:
        return pd.Series(dtype=float)
    
    try:
        # Handle MultiIndex columns from yfinance
        if isinstance(data.columns, pd.MultiIndex):
            # Get the first (and likely only) symbol's data
            adj_close_col = data['Adj Close'].iloc[:, 0] if len(data['Adj Close'].columns) > 0 else data['Adj Close']
        else:
            adj_close_col = data['Adj Close']
        
        # Validate data
        if len(adj_close_col) < 2:
            return pd.Series(dtype=float)
        
        # Create a copy to avoid modifying original data
        data_copy = data.copy()
        data_copy['Year'] = data_copy.index.year
        data_copy['Year'] = data_copy['Year'].astype(str)  # Convert 'Year' to string type
        data_copy['Adj_Close'] = adj_close_col
        
        # Filter out invalid data
        data_copy = data_copy.dropna(subset=['Adj_Close'])
        data_copy = data_copy[data_copy['Adj_Close'] > 0]
        
        if len(data_copy) < 2:
            return pd.Series(dtype=float)
        
        yearly_prices = data_copy.groupby('Year')['Adj_Close'].agg(['first', 'last'])
        
        # Filter out years with insufficient data
        yearly_prices = yearly_prices.dropna()
        
        if len(yearly_prices) == 0:
            return pd.Series(dtype=float)
        
        yearly_returns = (yearly_prices['last'] / yearly_prices['first'] - 1) * 100
        return yearly_returns.round(2)
    except Exception as e:
        st.error(f"Error calculating annual returns: {str(e)}")
        return pd.Series(dtype=float)

# Fetching data
stock_data = fetch_data(symbol_input, start_date, end_date)
benchmark_data = fetch_data(benchmark_input, start_date, end_date)

# Check if data was successfully fetched
if stock_data is not None and benchmark_data is not None:
    # Calculating metrics
    stock_cagr, stock_gain = calculate_metrics(stock_data)
    benchmark_cagr, benchmark_gain = calculate_metrics(benchmark_data)

    # Displaying metrics
    if stock_cagr is not None and benchmark_cagr is not None:
        st.header(f"{symbol_input} and {benchmark_input} metrics")
        metrics_df = pd.DataFrame({
            'Metric': ['CAGR (%)', 'Overall Gain (%)'],
            symbol_input: [stock_cagr, stock_gain],
            benchmark_input: [benchmark_cagr, benchmark_gain]
        })
        st.table(metrics_df)

        # Calculating and displaying annual returns
        stock_annual_returns = calculate_annual_returns(stock_data)
        benchmark_annual_returns = calculate_annual_returns(benchmark_data)
        
        if not stock_annual_returns.empty and not benchmark_annual_returns.empty:
            annual_returns_df = pd.DataFrame({
                f'{symbol_input} Annual Returns (%)': stock_annual_returns,
                f'{benchmark_input} Annual Returns (%)': benchmark_annual_returns
            })
            annual_returns_df['Outcome'] = np.where(annual_returns_df[f'{symbol_input} Annual Returns (%)'] > annual_returns_df[f'{benchmark_input} Annual Returns (%)'], 'Outperform', 'Underperform')

            st.header('Annual Returns and Outcome')
            st.dataframe(annual_returns_df)
        else:
            st.warning("Unable to calculate annual returns for one or both symbols.")
    else:
        st.error("Unable to calculate metrics for one or both symbols.")
else:
    st.error("Failed to fetch data for one or both symbols. Please check the symbols and try again.")

# Instructions for running: Save this script and run using the command: streamlit run finance_tool_cagr_outcome_streamlit.py





