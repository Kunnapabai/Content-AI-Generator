"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/bing/bulk_traffic_estimation/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/bing/bulk_traffic_estimation/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'targets': [
            'dataforseo.com',
            'cnn.com',
            'forbes.com'
        ],
        'location_code': 2840,
        'language_code': 'en',
        'item_types': [
            'organic',
            'paid'
        ]
    })
try:
    response = client.post('/v3/dataforseo_labs/bing/bulk_traffic_estimation/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
