"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/google/app_intersection/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/google/app_intersection/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'app_ids': {
            1: 'org.telegram.messenger',
            2: 'com.whatsapp'
        },
        'language_code': 'en',
        'location_code': 2840,
        'filters': [
            'keyword_data.keyword_info.search_volume',
            '>',
            10000
        ],
        'order_by': [
            'keyword_data.keyword_info.search_volume,desc'
        ],
        'limit': 10
    })
try:
    response = client.post('/v3/dataforseo_labs/google/app_intersection/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
