import streamlit as st
import asyncio
import requests
from pprint import pprint

# Capital.com API endpoints
session_api_url = "https://demo-api-capital.backend-capital.com/api/v1/session"

def create_session(api_key, identifier, password):
    """Creates a session, saves tokens to a Python file, and returns the tokens."""
    session_headers = {
        'X-CAP-API-KEY': api_key,
        'Content-Type': 'application/json'
    }

    session_payload = {
        "identifier": identifier,
        "password": password
    }

    st.write("Session Headers:", session_headers)
    st.write("Session Payload:", session_payload)

    response = requests.post(session_api_url, headers=session_headers, json=session_payload)

    if response.status_code == 200:
        data = response.json()
        st.write("Session creation response:", data)  # Print the full response for debugging
        balance = data.get('accountInfo', {}).get('balance')  # Extract balance from accountInfo or default to 0
        cst_token = response.headers.get('CST')
        security_token = response.headers.get('X-SECURITY-TOKEN')

        if not cst_token or not security_token:
            st.error("Failed to retrieve CST or security token.")
            return None, None, None

        return balance, cst_token, security_token
    else:
        st.error(f"Failed to create session. Status code: {response.status_code}")
        st.error(response.text)
        return None, None, None

def get_filtered_symbols(cst_token, security_token):
    """Retrieves and filters market symbols based on specified criteria.

    Args:
        cst_token: The CST token for authentication.
        security_token: The security token for authentication.

    Returns:
        A list of filtered symbols that meet the criteria.
    """
    node_ids = [
        "hierarchy_v1.shares.us.most_traded",
        "hierarchy_v1.shares.us.top_gainers",
        "hierarchy_v1.shares.us.top_losers",
        "hierarchy_v1.shares.us.most_volatile"
    ]
    # Define the headers with the tokens for authentication
    headers = {
        'X-SECURITY-TOKEN': security_token,
        'CST': cst_token
    }

    filtered_symbols = []  # Store symbols that meet the criteria

    for node_id in node_ids:
        url = f"https://api-capital.backend-capital.com/api/v1/marketnavigation/{node_id}"

        # Make the API request
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            market_navigation_data = response.json()  # Parse the JSON response
            pprint(market_navigation_data)

            # Iterate through markets and extract relevant data
            for market in market_navigation_data.get('markets', []):
                symbol = market.get('epic')
                bid = market.get('bid')
                offer = market.get('offer')

                # Check if the market meets the filtering criteria
                if bid is not None and offer is not None and offer - bid < 0.2 and bid > 80:
                    filtered_symbols.append((symbol, round(offer - bid, 2)))

        else:  # Handle cases where the request was not successful
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)  # Print the error response for debugging

    return filtered_symbols

def fetch_historical_prices(cst_token, security_token, epic, resolution='D', max_results=14):
    """Fetches historical prices for the given epic."""
    headers = {
        'X-CAP-API-KEY': st.secrets["capitalcom"]["api_key"],
        'CST': cst_token,
        'X-SECURITY-TOKEN': security_token
    }
    url = f"https://demo-api-capital.backend-capital.com/api/v1/prices/{epic}?resolution={resolution}&max={max_results}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()['prices']
    else:
        st.error(f"Failed to fetch historical prices for {epic}. Status code: {response.status_code}")
        st.error(response.text)
        return None

def calculate_atr(prices):
    """Calculates the Average True Range (ATR) from historical prices."""
    tr_values = []
    for i in range(1, len(prices)):
        high = prices[i]['highPrice']['bid']
        low = prices[i]['lowPrice']['bid']
        prev_close = prices[i-1]['closePrice']['bid']
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        tr_values.append(tr)
    atr = sum(tr_values) / len(tr_values)
    return atr

# Streamlit app
st.title("Capital.com REST API Stream")

# Load secrets from st.secrets
api_key = st.secrets["capitalcom"]["api_key"]
identifier = st.secrets["capitalcom"]["identifier"]
password = st.secrets["capitalcom"]["password"]

# Button to start fetching prices
if st.button("Fetch Prices"):
    balance, cst_token, security_token = create_session(api_key, identifier, password)
    if cst_token and security_token:
        st.write(f"Balance: {balance}")
        st.write(f"CST Token: {cst_token}")
        st.write(f"Security Token: {security_token}")
        filtered_symbols = get_filtered_symbols(cst_token, security_token)
        st.write("Filtered Symbols:")
        for symbol, spread in filtered_symbols:
            st.write(f"Symbol: {symbol}, Spread: {spread}")
            prices = fetch_historical_prices(cst_token, security_token, symbol)
            if prices:
                atr = calculate_atr(prices)
                st.write(f"Symbol: {symbol}, ATR: {atr}")