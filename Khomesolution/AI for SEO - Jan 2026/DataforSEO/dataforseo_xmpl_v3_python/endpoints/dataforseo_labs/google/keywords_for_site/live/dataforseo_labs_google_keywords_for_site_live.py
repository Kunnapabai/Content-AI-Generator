"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/google/keywords_for_site/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/google/keywords_for_site/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'target': 'apple.com',
        'language_code': 'en',
        'location_code': 2840,
        'include_serp_info': True,
        'include_subdomains': True,
        'filters': [
            'serp_info.se_results_count',
            '>',
            0
        ],
        'order_by': [
            'relevance,desc',
            'keyword_info.search_volume,desc'
        ],
        'limit': 3
    })
try:
    response = client.post('/v3/dataforseo_labs/google/keywords_for_site/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
