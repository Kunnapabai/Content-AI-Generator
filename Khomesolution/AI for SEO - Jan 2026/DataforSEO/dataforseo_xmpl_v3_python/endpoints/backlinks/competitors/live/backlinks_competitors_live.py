"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/backlinks/competitors/live
@see https://docs.dataforseo.com/v3/backlinks/competitors/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'target': 'dataforseo.com',
        'order_by': [
            'rank,desc'
        ],
        'filters': [
            [
                'rank',
                '>',
                100
            ]
        ],
        'limit': 10
    })
try:
    response = client.post('/v3/backlinks/competitors/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
