import requests 
import json 
from datetime import datetime, timedelta
import re


class PolymarketError(Exception):
    """Base exception for Polymarket API errors."""
    pass


class InvalidURLError(PolymarketError):
    """Raised when the provided URL is invalid."""
    pass


class APIRequestError(PolymarketError):
    """Raised when API request fails."""
    pass


def parse_date(date_input):
    """Convert various date formats to datetime object."""
    if isinstance(date_input, datetime):
        return date_input
        
    if isinstance(date_input, str):
        try:
            return datetime.fromisoformat(date_input.replace('Z', '+00:00'))
        except ValueError:
            pass

        for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m-%d-%Y', '%m/%d/%Y']:
            try:
                return datetime.strptime(date_input, fmt)
            except ValueError:
                continue
                
    raise ValueError(f"Could not parse date: {date_input}")


def extract_event_slug(url):
    """Extract the event slug from a Polymarket URL."""
    if "/event/" not in url:
        raise InvalidURLError(f"Invalid Polymarket URL: {url}. Must contain '/event/'")
    
    slug = url.split("/event/")[-1].strip()
    
    if not slug:
        raise InvalidURLError(f"Could not extract event slug from URL: {url}")
    
    return slug


def fetch_market_metadata(url, timeout=10):
    """Fetch market metadata from Polymarket API."""
    slug = extract_event_slug(url)
    api_url = f"https://gamma-api.polymarket.com/events?slug={slug}"
    
    try:
        response = requests.get(api_url, timeout=timeout)
        response.raise_for_status()
    except requests.Timeout:
        raise APIRequestError(f"Request timed out after {timeout} seconds")
    except requests.RequestException as e:
        raise APIRequestError(f"Failed to fetch market data: {e}")
    
    data = response.json()
    
    if not data:
        raise APIRequestError(f"No market data found for slug: {slug}")
    
    event = data[0]
    markets = event.get('markets', [])
    
    if not markets:
        raise APIRequestError(f"No markets found in event: {slug}")
    
    result = {}
    for market in markets:
        result[market['question']] = {
            "start_date": market.get('startDate'), 
            "end_date": market.get('closedTime'),      
            "condition_id": market['conditionId'],
            "clob_token_ids": market['clobTokenIds']
        }
    
    return result


def remove_placeholder_markets(market_dict):
    """Remove generic placeholder markets (e.g., "Candidate A", "Movie B")."""
    filtered_markets = {}
    
    # Pattern matches single letters used as placeholders
    placeholder_pattern = r'\b[a-z][\s"\)]\s*(be|win|lose|"|$)'
    
    for question, metadata in market_dict.items():
        has_placeholder = re.search(placeholder_pattern, question.lower())
        
        if not has_placeholder:
            filtered_markets[question] = metadata
    
    return filtered_markets


def fetch_price_history(token_id, fidelity, start_date, end_date, timeout=10):
    """
    Fetch historical price data for a single token from Polymarket.
    
    Polymarket API limits responses to 15-day chunks, so this function
    automatically handles pagination.
    
    Args:
        token_id (str): The market token identifier
        fidelity (int): Data granularity in minutes (e.g., 60 for hourly)
        start_date (str or datetime): Start date
        end_date (str or datetime): End date
        timeout (int): Request timeout in seconds
        
    Returns:
        list: Historical price data points
        
    Raises:
        APIRequestError: If API request fails
    """
    base_url = "https://clob.polymarket.com/prices-history"
    
    current_start = parse_date(start_date)
    end = parse_date(end_date)
    full_data = []
    
    # Fetch data in 15-day chunks (API limitation)
    while current_start < end:
        chunk_end = min(current_start + timedelta(days=15), end)
        
        params = {
            "market": token_id,
            "startTs": int(current_start.timestamp()),
            "endTs": int(chunk_end.timestamp()),
            "fidelity": fidelity
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            if 'history' in data:
                full_data.extend(data['history'])
            
        except requests.Timeout:
            raise APIRequestError(f"Request timed out after {timeout} seconds")
        except requests.RequestException as e:
            raise APIRequestError(f"Failed to fetch price history: {e}")
        
        current_start = chunk_end
    
    return full_data


def fetch(url, fidelity=60, exclude_placeholders=True, timeout=10):
    """
    Fetch historical price data for all markets in a Polymarket event.
    
    Args:
        url (str): Polymarket event URL (e.g., "https://polymarket.com/event/...")
        fidelity (int): Data granularity in minutes (default: 60 for hourly data)
        exclude_placeholders (bool): Remove generic "Candidate A" style markets
        timeout (int): Request timeout in seconds
        
    Returns:
        dict: Market questions mapped to their historical price data
        
    Raises:
        InvalidURLError: If URL is invalid
        APIRequestError: If API requests fail
        ValueError: If no valid markets found
        
    Example:
        >>> data = get_market_history("https://polymarket.com/event/...")
        >>> for question, prices in data.items():
        ...     print(f"{question}: {len(prices)} data points")
    """

    # fetch market metadata
    markets = fetch_market_metadata(url, timeout=timeout)
    
    # filter out placeholder markets if requested
    if exclude_placeholders:
        markets = remove_placeholder_markets(markets)
    
    if not markets:
        raise ValueError("No valid markets found after filtering")
    
    # determine date range across all markets
    start_dates = []
    end_dates = []
    
    for market_info in markets.values():
        if market_info['start_date']:
            start_dates.append(market_info['start_date'])
        if market_info['end_date']:
            end_dates.append(market_info['end_date'])
    
    if not start_dates or not end_dates:
        raise ValueError("Markets are missing start/end dates")
    
    min_start_date = min(start_dates)
    max_end_date = max(end_dates)
    
    # fetch historical data for each market
    historical_data = {}
    
    for question, market_info in markets.items():
        token_ids = json.loads(market_info['clob_token_ids'])
        primary_token_id = token_ids[0]  # usse first token (YES outcome)
        
        try:
            historical_data[question] = fetch_price_history(
                token_id=primary_token_id,
                fidelity=fidelity,
                start_date=min_start_date,
                end_date=max_end_date,
                timeout=timeout
            )
        except APIRequestError as e:
            print(f"Warning: Failed to fetch history for '{question}': {e}")
            continue
    
    return historical_data

