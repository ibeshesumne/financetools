import os
import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import matplotlib.pyplot as plt

# Constants
risk_free_rate = 0.01  # Risk-free rate, assuming 1% annual rate

# Streamlit app starts here
st.set_page_config(layout="wide")  # Use the full screen width
st.title('Stock Analysis Dashboard')

# Sidebar for user inputs
with st.sidebar:
    st.header('User Inputs')
    # User inputs several stocks separated by a comma
    stocks_input = st.text_input("Enter stock symbols separated by a comma")
    stocks = [stock.strip() for stock in stocks_input.split(',')] if stocks_input else []
    start_date = st.date_input('Start Date', value=pd.to_datetime('2023-01-01'))
    end_date = st.date_input('End Date', value=pd.to_datetime('2024-12-31'))
    index = st.text_input('Benchmark Symbol', value='^HSI')  # User input for index

# Check if stocks list is not empty
if not stocks:
    st.write("Please enter at least one stock symbol.")
else:

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

# Plotting
    # Extract the benchmark's CAGR and Annualized Volatility
    benchmark_cagr = index_metrics['CAGR']
    benchmark_stddev = index_metrics['Annualized Volatility']


    # Use Streamlit columns to control the layout
    col1, col2 = st.columns([3, 1])  # Creates two columns, using 3/4 of the width for the first and 1/4 for the second

    with col1:  # This block will use 3/4 of the width
        # Initialize the plot with specified dimensions
        fig, ax = plt.subplots(figsize=(10, 6))  # You can adjust the figsize to better fit the column width if necessary


        # Iterate over the DataFrame to plot each symbol
        for i, row in results.iterrows():
            ax.scatter(row['Annualized Volatility'], row['CAGR'], label=row['Symbol'])
            # Optionally, annotate the point with the symbol's name
            ax.text(row['Annualized Volatility'], row['CAGR'], row['Symbol'], color='black', ha='right', va='bottom')

        # Set plot title and labels
        ax.set_title('Stock Returns vs. Standard Deviation')
        ax.set_xlabel('Standard Deviation of Daily Returns (%)')
        ax.set_ylabel('Compounded Annual Growth Rate (%)')

        # Add legend to the plot
        #ax.legend()

        # Draw a vertical line for benchmark's standard deviation and a horizontal line for benchmark's CAGR
        ax.axvline(x=benchmark_stddev, color='lightgrey', linestyle='--')
        ax.axhline(y=benchmark_cagr, color='lightgrey', linestyle='--')

        # Display the plot in the Streamlit app
        st.pyplot(fig)
