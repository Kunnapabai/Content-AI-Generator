"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/google/page_intersection/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/google/page_intersection/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'pages': {
            1: 'https://forbes.com',
            2: 'https://cnn.com/*'
        },
        'language_name': 'English',
        'location_code': 2840,
        'include_serp_info': True,
        'limit': 3
    })
try:
    response = client.post('/v3/dataforseo_labs/google/page_intersection/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
