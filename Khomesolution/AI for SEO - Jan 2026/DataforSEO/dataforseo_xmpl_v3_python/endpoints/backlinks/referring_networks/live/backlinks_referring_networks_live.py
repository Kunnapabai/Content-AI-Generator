"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/backlinks/referring_networks/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'target': 'backlinko.com',
        'network_address_type': 'subnet',
        'limit': 5,
        'order_by': [
            'rank,desc'
        ],
        'exclude_internal_backlinks': True,
        'backlinks_filters': [
            'dofollow',
            '=',
            True
        ],
        'filters': [
            'backlinks',
            '>',
            100
        ]
    })
try:
    response = client.post('/v3/backlinks/referring_networks/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
