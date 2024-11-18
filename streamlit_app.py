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


def user_search(client_name):
    global smart_api
    config = load_config()
    
    # Find the user in the config
    user_found = False
    for user in config['User']:
        name = user['name']
        id_name = user['username']
        apikey = user['apikey']
        pwd = user['password']
        token = user['token']
        qty = user['qty']

        if name == client_name:  # Check if the current user's name matches the provided username
            user_found = True    
            #print('Details fetching for:', name)
            return(id_name, apikey, pwd, token,qty)
            break
        
    if not user_found:
        print(f"User '{client_name}' not found in configuration.")


def get_current_time():
    # Get the current time
    now = datetime.now()
    
    # Format the time as "YYYY-MM-DD HH:MM"
    formatted_time = now.strftime("%Y-%m-%d %H:%M")    
    return formatted_time


def fetch_data():
    #Historic api
    username, apikey, pwd, token, qty = user_search("Shayak")
    auth_token, feed_token =login_new(username, apikey, pwd, token)
    try:
        historicParam={
        "exchange": "NSE",
        "symboltoken": "99926000",
        "interval": "ONE_HOUR",
        "fromdate": "2024-10-15 09:15", 
        "todate": get_current_time()
        }
        candledata = smart_api.getCandleData(historicParam)
        column_names = ['time', 'open', 'high', 'low', 'close', "volume"]
        candledata_df = pd.DataFrame(candledata['data'], columns = column_names)
    except Exception as e:
        print("Historic Api failed: {}".format(e.message))


    candledata_df['rsi'] = ta.rsi(candledata_df['close'],14)

    last_row = candledata_df.iloc[-1]
    dt= datetime.fromisoformat(last_row['time'])
    formatted_date_time = dt.strftime('%Y-%m-%d %H:%M:%S')
    print("Current time:",formatted_date_time,"RSI:",round(last_row['rsi'],2))
    return(round(last_row['rsi'],2))

rsi_val = fetch_data()



#publishing on the web app

#st.button("Refresh")
st.set_page_config(layout="wide")
st.title("Algo Trade: Trend Following :fire:")
st.write("Showcasing the features that are already done")
st.header("Live Positions")
st.write("Current time:")
#st.write("Current time:",formatted_date_time,"RSI:",round(last_row['rsi'],2))

# Set the page configuration to wide mode

df = get_all_user_positions()
# Display the DataFrame
st.dataframe(df, width=1500, height=1000)  # Adjust width and height as needed



