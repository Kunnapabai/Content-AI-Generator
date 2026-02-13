"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/google/keywords_for_app/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/google/keywords_for_app/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'app_id': 'com.whatsapp',
        'language_name': 'English',
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
    response = client.post('/v3/dataforseo_labs/google/keywords_for_app/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
