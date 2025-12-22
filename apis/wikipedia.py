import requests
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

def get_pageviews(page_title, start_date, end_date):
    """
    Get daily pageviews for a Wikipedia page within a timeframe.
    Args:
        page_title (str): The title of the Wikipedia page.
        start_date (str or datetime): Start date (e.g., '2024-01-01', '01/01/2024').
        end_date (str or datetime): End date (e.g., '2024-12-31', '12/31/2024').
    """
    start = parse_date(start_date)
    end = parse_date(end_date)
    
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{page_title}/daily/{start.strftime('%Y%m%d')}/{end.strftime('%Y%m%d')}"
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; MyApp/1.0)'}
    response = requests.get(url, headers=headers)
    data = response.json()
    return data

def get_revisions(page_title, start_date, end_date):
    """
    Get revision history for a Wikipedia page within a timeframe.
    Args:
        page_title (str): The title of the Wikipedia page.
        start_date (str or datetime): Start date (e.g., '2024-01-01', '01/01/2024').
        end_date (str or datetime): End date (e.g., '2024-12-31', '12/31/2024').
    """
    start = parse_date(start_date)
    end = parse_date(end_date)
    
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        'action': 'query',
        'titles': page_title,
        'prop': 'revisions',
        'rvprop': 'ids|timestamp|user|comment|size',
        'rvstart': end.strftime('%Y-%m-%dT23:59:59Z'),  # ISO 8601 with time
        'rvend': start.strftime('%Y-%m-%dT00:00:00Z'),
        'rvlimit': 500,
        'format': 'json'
    }
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; MyApp/1.0)'}
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    page = list(data['query']['pages'].values())[0]
    revisions = page.get('revisions', [])
    return revisions