import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf
import time  # Add this line

# App title
st.title('Equity Performance')

# Sidebar inputs
symbol_input = st.sidebar.text_input('Enter Stock Symbol', 'BE')
benchmark_input = st.sidebar.text_input('Enter Benchmark Symbol', '^IXIC')
start_date = st.sidebar.date_input('Start Date', value=pd.to_datetime('2010-01-01'))
end_date = st.sidebar.date_input('End Date', value=pd.to_datetime('2024-12-31'))

# Function to fetch data
def fetch_data(symbol, start_date, end_date):
    data = yf.download(symbol, start=start_date, end=end_date)
    return data

# Function to calculate CAGR and overall gain
def calculate_metrics(data):
    if not data.empty:
        first_price = data['Adj Close'].iloc[0]
        last_price = data['Adj Close'].iloc[-1]
        days = (data.index[-1] - data.index[0]).days
        cagr = ((last_price / first_price) ** (365.25 / days) - 1) * 100
        overall_gain = ((last_price - first_price) / first_price) * 100
        return round(cagr, 2), round(overall_gain, 2)
    else:
        return None, None

# Function to calculate annual returns
def calculate_annual_returns(data):
    data['Year'] = data.index.year
    data['Year'] = data['Year'].astype(str)  # Convert 'Year' to string type
    yearly_prices = data.groupby('Year')['Adj Close'].agg(['first', 'last'])
    yearly_returns = (yearly_prices['last'] / yearly_prices['first'] - 1) * 100
    return yearly_returns.round(2)

# Fetching data
stock_data = fetch_data(symbol_input, start_date, end_date)
time.sleep(2)  # Wait for 2 seconds
benchmark_data = fetch_data(benchmark_input, start_date, end_date)
time.sleep(2)  # Wait for 2 seconds

# Calculating metrics
stock_cagr, stock_gain = calculate_metrics(stock_data)
benchmark_cagr, benchmark_gain = calculate_metrics(benchmark_data)

# Displaying metrics
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
annual_returns_df = pd.DataFrame({
    f'{symbol_input} Annual Returns (%)': stock_annual_returns,
    f'{benchmark_input} Annual Returns (%)': benchmark_annual_returns
})
annual_returns_df['Outcome'] = np.where(annual_returns_df[f'{symbol_input} Annual Returns (%)'] > annual_returns_df[f'{benchmark_input} Annual Returns (%)'], 'Outperform', 'Underperform')

st.header('Annual Returns and Outcome')
st.dataframe(annual_returns_df)

# Instructions for running: Save this script and run using the command: streamlit run financial_analysis_app.py




