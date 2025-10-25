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
        if data.empty:
            st.write(f"No data for {symbol}, skipping.")
            return None, None
        
        # Get the price column using the helper function
        adj_close_col = get_adj_close_column(data)
        if adj_close_col is None:
            st.error(f"Cannot extract price data for {symbol}")
            return None, None
        
        daily_returns = adj_close_col.pct_change().dropna()
        
        # Ensure all calculations result in scalars
        volatility = float(daily_returns.std()) * np.sqrt(252)
        mean_daily_return = float(daily_returns.mean())
        annualized_return = float((1 + mean_daily_return) ** 252 - 1)
        sharpe_ratio = float((annualized_return - risk_free_rate) / volatility)

        # Calculate CAGR as scalar
        cagr_value = float(((float(adj_close_col.iloc[-1]) / float(adj_close_col.iloc[0])) ** (365.25 / (data.index[-1] - data.index[0]).days) - 1) * 100)
        volatility_value = float(volatility * 100)
        sharpe_value = float(sharpe_ratio)
        
        metrics = {
            'Symbol': str(symbol),
            'CAGR': round(float(cagr_value), 2),
            'Annualized Volatility': round(float(volatility_value), 2),
            'Sharpe Ratio': round(float(sharpe_value), 2)
        }
        return data, metrics
    except Exception as e:
        st.error(f"Error processing {symbol}: {str(e)}")
        return None, None


# Function to calculate annual returns
def calculate_annual_returns(data):
    try:
        # Get the price column using the helper function
        adj_close_col = get_adj_close_column(data)
        if adj_close_col is None:
            return pd.Series(dtype=float)
        
        # Validate data
        if len(adj_close_col) < 2:
            return pd.Series(dtype=float)
        
        # Create a simple DataFrame with just the data we need
        # This avoids issues with MultiIndex DataFrames
        simple_df = pd.DataFrame({
            'Date': data.index,
            'Price': adj_close_col.values,
            'Year': data.index.year
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
        # Ensure both series are properly aligned and have the same index
        if not stock_annual_returns.empty and not index_annual_returns.empty:
            # Align the series by their common index
            common_index = stock_annual_returns.index.intersection(index_annual_returns.index)
            if len(common_index) > 0:
                stock_aligned = stock_annual_returns.loc[common_index]
                index_aligned = index_annual_returns.loc[common_index]
                
                annual_returns_df = pd.DataFrame({
                    f'{stock_symbol} Annual Returns (%)': stock_aligned,
                    f'{index} Annual Returns (%)': index_aligned
                })
                
                # Determine outcome
                annual_returns_df['Outcome'] = np.where(
                    annual_returns_df[f'{stock_symbol} Annual Returns (%)'] > annual_returns_df[f'{index} Annual Returns (%)'],
                    'Outperform',
                    'Underperform'
                )

                st.header('Annual Returns and Outcome')
                st.dataframe(annual_returns_df.style.map(lambda x: 'background-color : yellow' if x=='Outperform' else ''))  # Highlight 'Outperform' with yellow color
            else:
                st.warning("No common years found between stock and benchmark data")
        else:
            st.warning("Unable to calculate annual returns for one or both symbols")

    # Plotting
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
        ax.legend()

        # Draw a vertical line for benchmark's standard deviation and a horizontal line for benchmark's CAGR
        ax.axvline(x=benchmark_stddev, color='lightgrey', linestyle='--')
        ax.axhline(y=benchmark_cagr, color='lightgrey', linestyle='--')

        # Display the plot in the Streamlit app
        st.pyplot(fig)

    