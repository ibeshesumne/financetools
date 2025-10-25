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
    # List all CSV files in the directory
    csv_files = ['Select a file...'] + [f for f in os.listdir() if f.endswith('.csv')]
    selected_file = st.selectbox("Choose a CSV file", csv_files)
    start_date = st.date_input('Start Date', value=pd.to_datetime('2023-01-01'))
    end_date = st.date_input('End Date', value=pd.to_datetime('2024-12-31'))
    index = st.text_input('Benchmark Symbol', value='^HSI')  # User input for index

if selected_file != 'Select a file...':
    stocks_df = pd.read_csv(selected_file)
    stocks = stocks_df['Symbol'].tolist()

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
            # Suppress yfinance download messages
            import warnings
            import sys
            from io import StringIO
            
            # Capture stdout to suppress progress messages
            old_stdout = sys.stdout
            sys.stdout = StringIO()
            
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    data = yf.download(symbol, start=start_date, end=end_date, auto_adjust=True, progress=False)
            finally:
                # Restore stdout
                sys.stdout = old_stdout
            
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
            
            # Validate we have enough data
            if len(adj_close_col) < 2:
                st.write(f"Insufficient data for {symbol}, skipping.")
                return None
            
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
            # Only show error for unexpected issues, not for common download failures
            if "YFTzMissingError" in str(e) or "delisted" in str(e).lower() or "timezone" in str(e).lower():
                st.write(f"Symbol {symbol} may be delisted or unavailable, skipping.")
            else:
                st.write(f"Error processing {symbol}: {str(e)}")
            return None

    # Fetch and process data
    st.write(f"Processing {len(stocks)} stocks...")
    
    # Create progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    index_metrics = fetch_and_calculate(index, start_date, end_date)
    
    if index_metrics is not None:
        stock_metrics = []
        failed_symbols = []
        
        for i, stock in enumerate(stocks):
            status_text.text(f"Processing {stock} ({i+1}/{len(stocks)})")
            progress_bar.progress((i + 1) / len(stocks))
            
            metric = fetch_and_calculate(stock, index_metrics['First Trading Day'], end_date)
            if metric is not None:
                stock_metrics.append(metric)
            else:
                failed_symbols.append(stock)
        
        # Show summary of failed downloads
        if failed_symbols:
            st.write(f"Note: {len(failed_symbols)} symbols could not be processed (possibly delisted or unavailable): {', '.join(failed_symbols[:10])}{'...' if len(failed_symbols) > 10 else ''}")
        
        # Clear progress indicators
        progress_bar.empty()
        status_text.empty()

        # Create DataFrame
        results = pd.DataFrame([index_metrics] + stock_metrics)

        # Ensure index is always at the top
        results = pd.concat([results[results['Symbol'] == index], results[results['Symbol'] != index].sort_values(by='CAGR', ascending=False)])

        # Display results
        st.header("Results Summary:")
        st.dataframe(results)

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
    else:
        st.error("Failed to fetch benchmark data. Please check the symbol and try again.")

else:
    st.write("Please select a CSV file.")