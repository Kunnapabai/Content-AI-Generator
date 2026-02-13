"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/serp/google/dataset_search/live/advanced
@see https://docs.dataforseo.com/v3/serp/google/dataset_search/live/advanced
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'keyword': 'water quality',
        'last_updated': '1m',
        'file_formats': [
            'archive',
            'image'
        ],
        'usage_rights': 'noncommercial',
        'is_free': True,
        'topics': [
            'natural_sciences',
            'geo'
        ],
        'depth': 100
    })
try:
    response = client.post('/v3/serp/google/dataset_search/live/advanced', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
