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
    
    # User input for index
    index_options = [
        ('Hang Seng Index ^HSI', '^HSI'),
        ('Dow Jones Industrial Average ^DJI', '^DJI'),
        ('NASDAQ ^IXIC', '^IXIC'),
        ('S&P 500 ^GSPC', '^GSPC'),
        ('Nikkei ^N225', '^N225')
    ]
    index_name, index = st.selectbox('Select a Benchmark Symbol', index_options, format_func=lambda x: x[0])
    custom_index = st.text_input('Or enter a custom Benchmark Symbol')
    index = custom_index if custom_index else index
    st.markdown("For more indices, please refer to [Yahoo Finance World Indices](https://finance.yahoo.com/world-indices/)")

# Check if stocks list is not empty
if not stocks:
    st.write("Please enter at least one stock symbol.")
else:

    # Function to get adjusted close price column from yfinance data
    def get_adj_close_column(data):
        """Extract adjusted close price column from yfinance data, handling different data structures."""
        try:
            # Check if data has MultiIndex columns
            if isinstance(data.columns, pd.MultiIndex):
                # For MultiIndex, safely check for available columns
                available_levels = data.columns.levels[0].tolist()
                
                # Try to get Adj Close first
                if 'Adj Close' in available_levels:
                    try:
                        adj_close_col = data['Adj Close']
                        # If it's still a MultiIndex, get the first column
                        if isinstance(adj_close_col.columns, pd.MultiIndex):
                            adj_close_col = adj_close_col.iloc[:, 0]
                        return adj_close_col
                    except (KeyError, IndexError):
                        pass
                
                # If no Adj Close, try Close price
                if 'Close' in available_levels:
                    try:
                        close_col = data['Close']
                        # If it's still a MultiIndex, get the first column
                        if isinstance(close_col.columns, pd.MultiIndex):
                            close_col = close_col.iloc[:, 0]
                        return close_col
                    except (KeyError, IndexError):
                        pass
                
                # If neither works, try to get any available price column
                for level in available_levels:
                    if 'close' in level.lower() or 'price' in level.lower():
                        try:
                            price_col = data[level]
                            if isinstance(price_col.columns, pd.MultiIndex):
                                price_col = price_col.iloc[:, 0]
                            return price_col
                        except (KeyError, IndexError):
                            continue
                
                raise ValueError(f"No suitable price column found. Available levels: {available_levels}")
            else:
                # For regular columns
                if 'Adj Close' in data.columns:
                    return data['Adj Close']
                elif 'Close' in data.columns:
                    return data['Close']
                else:
                    # If neither exists, try to find any price column
                    price_cols = [col for col in data.columns if 'close' in col.lower() or 'price' in col.lower()]
                    if price_cols:
                        return data[price_cols[0]]
                    else:
                        raise ValueError(f"No suitable price column found. Available columns: {list(data.columns)}")
            
        except Exception as e:
            st.error(f"Error extracting price data: {str(e)}")
            return None

    # Function to fetch data and calculate metrics
    def fetch_and_calculate(symbol, start_date, end_date):
        try:
            data = yf.download(symbol, start=start_date, end=end_date, auto_adjust=True)
            if data.empty:  # Check if data is empty
                st.write(f"No data for {symbol}, skipping.")
                return None
            
            # Get the price column using the helper function
            adj_close_col = get_adj_close_column(data)
            if adj_close_col is None:
                st.write(f"Cannot extract price data for {symbol}, skipping.")
                return None
            
            # Ensure adj_close_col is a Series
            if isinstance(adj_close_col, pd.DataFrame):
                adj_close_col = adj_close_col.iloc[:, 0]
            
            daily_returns = adj_close_col.pct_change().dropna()  # Calculate daily returns
            volatility = float(daily_returns.std()) * np.sqrt(252)  # Annualized volatility
            mean_daily_return = float(daily_returns.mean())
            annualized_return = float((1 + mean_daily_return) ** 252 - 1)
            sharpe_ratio = float((annualized_return - risk_free_rate) / volatility)  # Calculate Sharpe Ratio

            first_day = data.index[0]
            last_day = data.index[-1]
            first_price = float(adj_close_col.iloc[0])
            last_price = float(adj_close_col.iloc[-1])
            days = (last_day - first_day).days
            cagr = float(((last_price / first_price) ** (365.25 / days) - 1) * 100)

            return {
                'Symbol': str(symbol),
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
        except Exception as e:
            st.error(f"Error processing {symbol}: {str(e)}")
            return None

    # Fetch and process data for benchmark first
    index_metrics = fetch_and_calculate(index, start_date, end_date)
    
    # Only proceed if benchmark data was successfully fetched
    if index_metrics is None:
        st.error(f"Failed to fetch benchmark data for {index}. Please check the symbol and try again.")
    else:
        # Fetch stock data using benchmark's first trading day
        stock_metrics = [metric for metric in (fetch_and_calculate(stock, index_metrics['First Trading Day'], end_date) for stock in stocks) if metric is not None]

        # Create DataFrame
        results = pd.DataFrame([index_metrics] + stock_metrics)

        # Ensure index is always at the top
        results = pd.concat([results[results['Symbol'] == index], results[results['Symbol'] != index].sort_values(by='CAGR', ascending=False)])

        # Display results
        st.header("Results Summary:")
        st.dataframe(results)

        # Function to calculate annual returns
        def calculate_annual_returns(data):
            if data is None or data.empty:
                return pd.Series(dtype=float)
            
            try:
                # Use the helper function to get the price column
                adj_close_col = get_adj_close_column(data)
                if adj_close_col is None:
                    return pd.Series(dtype=float)
                
                # Ensure adj_close_col is a Series
                if isinstance(adj_close_col, pd.DataFrame):
                    adj_close_col = adj_close_col.iloc[:, 0]
                
                # Convert to Series if it's not already
                if not isinstance(adj_close_col, pd.Series):
                    adj_close_col = pd.Series(adj_close_col, index=data.index)
                
                # Validate data
                if len(adj_close_col) < 2:
                    return pd.Series(dtype=float)
                
                # Create a simple DataFrame with just the data we need
                simple_df = pd.DataFrame({
                    'Date': adj_close_col.index,
                    'Price': adj_close_col.values.flatten(),  # Flatten to ensure 1D
                    'Year': adj_close_col.index.year
                })
                
                # Filter out invalid data
                simple_df = simple_df.dropna(subset=['Price'])
                simple_df = simple_df[simple_df['Price'] > 0]
                
                if len(simple_df) < 2:
                    return pd.Series(dtype=float)
                
                # Group by year and get first and last prices
                yearly_prices = simple_df.groupby('Year')['Price'].agg(['first', 'last'])
                
                # Filter out years with insufficient data
                yearly_prices = yearly_prices.dropna()
                
                if len(yearly_prices) == 0:
                    return pd.Series(dtype=float)
                
                yearly_returns = (yearly_prices['last'] / yearly_prices['first'] - 1) * 100
                return yearly_returns.round(2)
            except Exception as e:
                st.error(f"Error calculating annual returns: {str(e)}")
                return pd.Series(dtype=float)

        # Fetching data for annual returns
        if stocks:
            try:
                stock_data = yf.download(stocks[0], start=start_date, end=end_date)
                benchmark_data = yf.download(index, start=start_date, end=end_date)

                # Calculating and displaying annual returns
                stock_annual_returns = calculate_annual_returns(stock_data)
                benchmark_annual_returns = calculate_annual_returns(benchmark_data)

                if not stock_annual_returns.empty and not benchmark_annual_returns.empty:
                    # Align the series by their common index
                    common_index = stock_annual_returns.index.intersection(benchmark_annual_returns.index)
                    if len(common_index) > 0:
                        stock_aligned = stock_annual_returns.loc[common_index]
                        benchmark_aligned = benchmark_annual_returns.loc[common_index]
                        
                        annual_returns_df = pd.DataFrame({
                            f'{stocks[0]} Annual Returns (%)': stock_aligned,
                            f'{index} Annual Returns (%)': benchmark_aligned
                        })

                        st.header("Annual Returns:")
                        st.dataframe(annual_returns_df)
                    else:
                        st.warning("No common years found between stock and benchmark data.")
                else:
                    st.warning("Unable to calculate annual returns for one or both symbols.")
            except Exception as e:
                st.error(f"Error fetching data for annual returns: {str(e)}")

        # Plotting
        if not results.empty:
            try:
                # Extract the benchmark's CAGR and Annualized Volatility as scalar values
                benchmark_cagr = float(index_metrics['CAGR'])
                benchmark_stddev = float(index_metrics['Annualized Volatility'])

                # Use Streamlit columns to control the layout
                col1, col2 = st.columns([3, 1])  # Creates two columns, using 3/4 of the width for the first and 1/4 for the second

                with col1:  # This block will use 3/4 of the width
                    # Initialize the plot with specified dimensions
                    fig, ax = plt.subplots(figsize=(10, 6))  # You can adjust the figsize to better fit the column width if necessary

                    # Iterate over the DataFrame to plot each symbol
                    for i, row in results.iterrows():
                        # Ensure we have scalar values for plotting
                        volatility = float(row['Annualized Volatility'])
                        cagr = float(row['CAGR'])
                        symbol = str(row['Symbol'])
                        
                        ax.scatter(volatility, cagr, label=symbol)
                        # Optionally, annotate the point with the symbol's name
                        ax.text(volatility, cagr, symbol, color='black', ha='right', va='bottom')

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
            except Exception as e:
                st.error(f"Error creating plot: {str(e)}")
        else:
            st.warning("Unable to create plot due to missing data.")