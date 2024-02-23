import os
import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st

# Constants
risk_free_rate = 0.01  # Risk-free rate, assuming 1% annual rate

# Streamlit app starts here
st.set_page_config(layout="wide")  # Use the full screen width
st.title('Stock Analysis Dashboard')

# Sidebar for user inputs
with st.sidebar:
    st.header('User Inputs')
    # List all CSV files in the directory
    csv_files = [f for f in os.listdir() if f.endswith('.csv')]
    selected_file = st.selectbox("Choose a CSV file", csv_files)
    start_date = st.date_input('Start Date', value=pd.to_datetime('2010-01-01'))
    end_date = st.date_input('End Date', value=pd.to_datetime('2024-12-31'))
    index = st.text_input('Benchmark Symbol', value='^DJI')  # User input for index


if selected_file:
    stocks_df = pd.read_csv(selected_file)
    stocks = stocks_df['Symbol'].tolist()
    # Rest of the code remains the same

    # Function to fetch data and calculate metrics
    def fetch_and_calculate(symbol, start_date, end_date):
        data = yf.download(symbol, start=start_date, end=end_date)
        if data.empty:  # Check if data is empty
            st.write(f"No data for {symbol}, skipping.")
            return None
        daily_returns = data['Adj Close'].pct_change().dropna()  # Calculate daily returns
        volatility = daily_returns.std() * np.sqrt(252)  # Annualized volatility
        mean_daily_return = daily_returns.mean()
        annualized_return = (1 + mean_daily_return) ** 252 - 1
        sharpe_ratio = (annualized_return - risk_free_rate) / volatility  # Calculate Sharpe Ratio

        first_day = data.index[0]
        last_day = data.index[-1]
        first_price = data['Adj Close'].iloc[0]
        last_price = data['Adj Close'].iloc[-1]
        days = (last_day - first_day).days
        cagr = ((last_price / first_price) ** (365.25 / days) - 1) * 100

        return {
            'Symbol': symbol,
            'First Trading Day': first_day.date(),
            'First Trading Price': round(first_price, 2),
            'Last Trading Day': last_day.date(),
            'Last Trading Price': round(last_price, 2),
            'Number of Days': days,
            'CAGR': round(cagr, 2),
            'Overall Gain': round((last_price - first_price) / first_price * 100, 2),
            'Annualized Volatility': round(volatility * 100, 2),
            'Sharpe Ratio': round(sharpe_ratio, 2)
        }

    # Fetch and process data
    index_metrics = fetch_and_calculate(index, start_date, end_date)
    stock_metrics = [metric for metric in (fetch_and_calculate(stock, index_metrics['First Trading Day'], end_date) for stock in stocks) if metric is not None]

    # Create DataFrame
    results = pd.DataFrame([index_metrics] + stock_metrics)

    # Ensure index is always at the top
    results = pd.concat([results[results['Symbol'] == index], results[results['Symbol'] != index].sort_values(by='CAGR', ascending=False)])

    # Display results
    st.header("Results Summary:")
    st.dataframe(results)
else:
    st.write("Please upload a CSV file.")