import requests 
import json 


def get_historical_data(token, interval, fidelity, limit = 100):
    """
    Fetch historical price data for a given token from Polymarket.

    Args:
        token (str): The market token identifier.
        interval (str): Time window of historical data requested (e.g., '1d', '1w', '1m').
        fidelity (str): granularity of data points in minutes - integer
    """

    base_url = "https://clob.polymarket.com/prices-history" # base url for historical data

    params = {
        "market": token,
        "interval": interval,
        "fidelity": fidelity
        } # parameters for the API request

    # make the API request
    response = requests.get(base_url, params=params)

    data = response.json() # parse the JSON response

    return data


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
    

