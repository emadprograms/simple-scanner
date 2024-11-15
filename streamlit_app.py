import streamlit as st
import asyncio
import websockets
import json
import requests

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

# Function to connect to the websocket and fetch instrument prices
async def connect_to_websocket(cst_token, security_token):
    url = "wss://api-streaming-capital.backend-capital.com/connect"
    async with websockets.connect(url) as websocket:
        # Example subscription message (you may need to adjust this based on the API documentation)
        subscription_message = json.dumps({
            "destination": "marketData.subscribe",
            "correlationId": "1",
            "cst": cst_token,
            "securityToken": security_token,
            "payload": {
                "epics": ["GOOGL", "AAPL"]  # Replace with your desired instruments
            }
        })
        await websocket.send(subscription_message)

        # Create placeholders for the data
        googl_placeholder = st.empty()
        aapl_placeholder = st.empty()

        while True:
            response = await websocket.recv()
            data = json.loads(response)
            st.write(data)  # For debugging purposes, print the full response

            # Extract and display the prices for GOOGL and AAPL
            if data.get("destination") == "quote":
                epic = data["payload"]["epic"]
                bid = data["payload"]["bid"]
                ofr = data["payload"]["ofr"]
                if epic == "GOOGL":
                    googl_placeholder.write(f"GOOGL - Bid: {bid}, Offer: {ofr}")
                elif epic == "AAPL":
                    aapl_placeholder.write(f"AAPL - Bid: {bid}, Offer: {ofr}")

# Streamlit app
st.title("Capital.com WebSocket Stream")

# Load secrets from st.secrets
api_key = st.secrets["capitalcom"]["api_key"]
identifier = st.secrets["capitalcom"]["identifier"]
password = st.secrets["capitalcom"]["password"]

# Button to start WebSocket connection
if st.button("Connect to WebSocket"):
    balance, cst_token, security_token = create_session(api_key, identifier, password)
    if cst_token and security_token:
        st.write(f"Balance: {balance}")
        st.write(f"CST Token: {cst_token}")
        st.write(f"Security Token: {security_token}")
        asyncio.run(connect_to_websocket(cst_token, security_token))