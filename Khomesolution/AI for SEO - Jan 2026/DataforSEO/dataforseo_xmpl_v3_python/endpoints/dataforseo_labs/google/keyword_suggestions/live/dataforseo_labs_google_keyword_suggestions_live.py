"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/google/keyword_suggestions/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/google/keyword_suggestions/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'keyword': 'seo tool',
        'location_code': 2840,
        'language_code': 'en',
        'filters': [
            'serp_info.se_results_count',
            '>',
            0
        ],
        'order_by': [
            'keyword_info.search_volume,desc'
        ],
        'include_serp_info': True,
        'limit': 1
    })
try:
    response = client.post('/v3/dataforseo_labs/google/keyword_suggestions/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
