"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/bing/ranked_keywords/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/bing/ranked_keywords/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'target': 'bing.com',
        'language_name': 'English',
        'location_name': 'United States',
        'load_rank_absolute': True,
        'limit': 3
    })
try:
    response = client.post('/v3/dataforseo_labs/bing/ranked_keywords/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
