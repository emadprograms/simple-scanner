import yfinance as yf
import streamlit as st

# Define the ticker symbol
ticker_symbol = 'AAPL'

# Get data on this ticker
ticker_data = yf.Ticker(ticker_symbol)

# Get the historical prices for this ticker
ticker_df = ticker_data.history(period='1d', start='2020-1-1', end='2021-1-1')

# Display the data using Streamlit
st.write(ticker_df)