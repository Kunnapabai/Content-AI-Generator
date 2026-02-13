"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/keywords_data/bing/search_volume_history/live
@see https://docs.dataforseo.com/v3/keywords_data/bing/search_volume_history/live/?bash
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
        'keywords': [
            'seo',
            '10 minute timer'
        ],
        'period': 'weekly',
        'device': [
            'desktop'
        ]
    })
try:
    response = client.post('/v3/keywords_data/bing/search_volume_history/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
