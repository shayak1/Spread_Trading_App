# Step1: load all packages needed
from SmartApi import SmartConnect
import pandas as pd
import pyotp
import json
import time
import streamlit as st


# Step2:  Load configuration from JSON file
def load_config(file_path='config_all_users.json'):
    with open(file_path, 'r') as f:
        return json.load(f)

config = load_config()

# Step3 : define all functions
#.....login to smartapi..... 
def login_new (username, apikey, pwd, token): 
    global smart_api 
    smart_api = SmartConnect(apikey)
    try:
        # Generate TOTP token
        totp = pyotp.TOTP(token).now()  
        #print("Otp:", totp)
        
        # Login and generate session
        data = smart_api.generateSession(username, pwd, totp)
        #print(data)
        
        refresh_token = data['data']['refreshToken']
        auth_token = data['data']['jwtToken']
        feed_token = smart_api.getfeedToken()
        
        # print("Login successful!")
        return auth_token, feed_token
    except Exception as e:
        print(f"Login failed: {e}")

# log out from api 
def logout(username):
    try:
        logout=smart_api.terminateSession(username)
        print("Logout Successfull")
    except Exception as e:
        print(f"Logout failed: {e}")

import pandas as pd

def get_all_user_positions():
    global smart_api
    config = load_config()
    
    # List to hold position data for all users
    all_positions_data = []

    # Iterate through each user in the config
    for user in config['User']:
        name = user['name']
        id_name = user['username']
        apikey = user['apikey']
        pwd = user['password']
        token = user['token']
        qty = user['qty']
        
        # Authenticate
        auth_key, feed_key = login_new(id_name, apikey, pwd, token)
        try:
            positions = pd.DataFrame(smart_api.position())
            num_positions = len(positions)
            #print("Active positions for ---->", name)
            
            pnl_sum = 0
            
            for i in range(num_positions):
                if "NIFTY" in positions['data'][i]['tradingsymbol']:
                    trading_symbol = positions['data'][i]['tradingsymbol']
                    quantity = float(positions['data'][i]['netqty']) / 25
                    pnl = positions['data'][i]['pnl']
                    
                    # Append the data to the list with user name
                    all_positions_data.append({
                        "User": name,
                        "Trading Symbol": trading_symbol,
                        "Quantity (Lots)": quantity,
                        "PnL": pnl
                    })
                    
                    pnl_sum += float(pnl)

            # Append total PnL for the user to the list
            all_positions_data.append({
                "User": name,
                "Trading Symbol": "Total",
                "Quantity (Lots)": "",
                "PnL": pnl_sum
            })
        
        except Exception as e:
            print("No Positions for", name)
            # Optionally log the error message
            print(f"Error: {e}")

    # Create a DataFrame from the collected data for all users
    if all_positions_data:
        all_positions_df = pd.DataFrame(all_positions_data)
        print("\nConsolidated Active Positions for All Users:")
        return(all_positions_df)
    else:
        print("No positions found for any users.")


#st.button("Refresh")
st.set_page_config(layout="wide")
st.title("Algo Trade: Trend Following :fire:")
st.write("Showcasing the features that are already done")
st.header("Live Positions")

# Set the page configuration to wide mode

df = get_all_user_positions()
# Display the DataFrame
st.dataframe(df, width=1500, height=1000)  # Adjust width and height as needed



