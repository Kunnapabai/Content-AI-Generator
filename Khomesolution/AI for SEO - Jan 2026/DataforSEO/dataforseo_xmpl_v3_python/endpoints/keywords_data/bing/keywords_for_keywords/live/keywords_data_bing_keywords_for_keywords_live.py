"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/keywords_data/bing/keywords_for_keywords/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'location_code': 2840,
        'language_code': 'en',
        'sort_by': 'cpc',
        'keywords': [
            'pizza'
        ]
    })
try:
    response = client.post('/v3/keywords_data/bing/keywords_for_keywords/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
