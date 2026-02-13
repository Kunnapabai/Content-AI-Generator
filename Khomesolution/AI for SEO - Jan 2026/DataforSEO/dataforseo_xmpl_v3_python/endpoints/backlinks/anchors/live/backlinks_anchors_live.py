"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/backlinks/anchors/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'target': 'forbes.com',
        'limit': 4,
        'order_by': [
            'backlinks,desc'
        ],
        'filters': [
            'anchor',
            'like',
            '%news%'
        ]
    })
try:
    response = client.post('/v3/backlinks/anchors/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
