
import requests 
import json 

from datetime import datetime, timedelta

def parse_date(date_input):
    """Convert various date formats to datetime object."""
    if isinstance(date_input, datetime):
        return date_input
    if isinstance(date_input, str):
        # Try common formats
        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m-%d-%Y', '%m/%d/%Y']:
            try:
                return datetime.strptime(date_input, fmt)
            except ValueError:
                continue
    raise ValueError(f"Could not parse date: {date_input}")

def get_historical_data(token, fidelity, start_date, end_date):
    """
    Fetch historical price data for a given token from Polymarket.

    Args:
        token (str): The market token identifier.
        fidelity (str): granularity of data points in minutes - integer
        start_date (str or datetime): Start date (e.g., '2024-01-01', '01/01/2024').
        end_date (str or datetime): End date (e.g., '2024-12-31', '12/31/2024').
    """

    base_url = "https://clob.polymarket.com/prices-history" # base url for historical data

    # convert dates to datetime objects   
    current_start = parse_date(start_date)  
    end = parse_date(end_date)
    full_data = []

    # polymarket API limits data to 15-day chunks 
    # so we loop to get all data in 15-day increments
    while current_start < end:  
        end_time = current_start + timedelta(days=15)
        if end_time > end: 
            end_time = end
        
        start_ts = int(current_start.timestamp())
        end_ts = int(end_time.timestamp())
        
        params = {
            "market": token,
            "startTs": start_ts,
            "endTs": end_ts,
            "fidelity": fidelity
        }
        
        response = requests.get(base_url, params=params)
        data = response.json()
        
        full_data.extend(data['history'])  # Fixed: actually append data
        current_start = current_start + timedelta(days=15)


        return full_data

def get_tokens(url):
    """
    Given a Polymarket event URL, fetch the associated market questions, condition IDs, and clob token IDs.
    Args:
        url (str): Polymarket event URL.
    """

    # extrct slug 
    slug = url.split("/event/")[-1]

    # make the api call
    api_url = f"https://gamma-api.polymarket.com/events?slug={slug}" 
    response = requests.get(api_url)

    # dict placeholder for results
    result = {}

    if response.status_code == 200:
        data = response.json()
        
        if data:
            event = data[0]
            # Loop through each market
            for market in event.get('markets', []):
                # Store question, condition ID, and clob token IDs in the result dictionary
                result[market['question']] = {
                    "condition_id": market['conditionId'],
                    "clob_token_ids": market['clobTokenIds']
                }
        return result
    else: 
        print(f"Error: {response.status_code}")
        return None
    

