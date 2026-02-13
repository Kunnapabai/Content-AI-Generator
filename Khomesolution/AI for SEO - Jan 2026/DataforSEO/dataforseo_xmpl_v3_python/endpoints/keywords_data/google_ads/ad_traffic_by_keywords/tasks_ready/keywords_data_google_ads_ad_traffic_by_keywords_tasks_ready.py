"""
Method: GET
Endpoint: https://api.dataforseo.com/v3/keywords_data/google_ads/ad_traffic_by_keywords/tasks_ready
@see https://docs.dataforseo.com/v3/keywords\_data/google_ads/ad\_traffic\_by\_keywords/tasks\_ready
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

try:
    response = client.get('/v3/keywords_data/google_ads/ad_traffic_by_keywords/tasks_ready')
    print(response)
    # do something with get result
except Exception as e:
    print(f'An error occurred: {e}')
