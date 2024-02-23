import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import matplotlib.pyplot as plt

# Constants
default_stock_symbol = '0101.HK'
default_index = '^HSI'
risk_free_rate = 0.01

# Streamlit app starts here
st.set_page_config(layout="wide")  # Use the full screen width
st.title('Stock Analysis Dashboard')

# Sidebar for user inputs
with st.sidebar:
    st.header('User Inputs')
    stock_symbol = st.text_input('Stock Symbol', default_stock_symbol)
    index = st.text_input('Benchmark Index', default_index)
    start_date = st.sidebar.date_input('Start Date', value=pd.to_datetime('2010-01-01'))
    end_date = st.sidebar.date_input('End Date', value=pd.to_datetime('2024-12-31'))


# Function to fetch data and calculate metrics
def fetch_and_calculate(symbol, start_date, end_date):
    data = yf.download(symbol, start=start_date, end=end_date)
    if data.empty:
        st.write(f"No data for {symbol}, skipping.")
        return None, None
    daily_returns = data['Adj Close'].pct_change().dropna()
    volatility = daily_returns.std() * np.sqrt(252)
    mean_daily_return = daily_returns.mean()
    annualized_return = (1 + mean_daily_return) ** 252 - 1
    sharpe_ratio = (annualized_return - risk_free_rate) / volatility

    metrics = {
        'Symbol': symbol,
        'CAGR': round(((data['Adj Close'].iloc[-1] / data['Adj Close'].iloc[0]) ** (365.25 / (data.index[-1] - data.index[0]).days) - 1) * 100, 2),
        'Annualized Volatility': round(volatility * 100, 2),
        'Sharpe Ratio': round(sharpe_ratio, 2)
    }
    return data, metrics


# Function to calculate annual returns
def calculate_annual_returns(data):
    data['Year'] = data.index.year
    data['Year'] = data['Year'].astype(str)  # Convert 'Year' to string type
    yearly_prices = data.groupby('Year')['Adj Close'].agg(['first', 'last'])
    yearly_returns = (yearly_prices['last'] / yearly_prices['first'] - 1) * 100
    return yearly_returns.round(2)


# Fetch and process data for both the stock and the index
stock_data, stock_metrics = fetch_and_calculate(stock_symbol, start_date, end_date)
index_data, index_metrics = fetch_and_calculate(index, start_date, end_date)

if stock_metrics and index_metrics:
    # Create DataFrame for summary results
    results = pd.DataFrame([index_metrics, stock_metrics])

    st.header("Results Summary:")
    st.dataframe(results) 

    # Calculating annual returns for stock and benchmark
    if stock_data is not None and index_data is not None:
        stock_annual_returns = calculate_annual_returns(stock_data)
        index_annual_returns = calculate_annual_returns(index_data)

        # Combining the annual returns into one DataFrame for comparison
        annual_returns_df = pd.DataFrame({
            f'{stock_symbol} Annual Returns (%)': stock_annual_returns,
            f'{index} Annual Returns (%)': index_annual_returns
        })

        # Determine outcome
        annual_returns_df['Outcome'] = np.where(
            annual_returns_df[f'{stock_symbol} Annual Returns (%)'] > annual_returns_df[f'{index} Annual Returns (%)'],
            'Outperform',
            'Underperform'
        )

        st.header('Annual Returns and Outcome')
        st.dataframe(annual_returns_df.style.applymap(lambda x: 'background-color : yellow' if x=='Outperform' else ''))  # Highlight 'Outperform' with yellow color)

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
        ax.legend()

        # Draw a vertical line for benchmark's standard deviation and a horizontal line for benchmark's CAGR
        ax.axvline(x=benchmark_stddev, color='lightgrey', linestyle='--')
        ax.axhline(y=benchmark_cagr, color='lightgrey', linestyle='--')

        # Display the plot in the Streamlit app
        st.pyplot(fig)

    