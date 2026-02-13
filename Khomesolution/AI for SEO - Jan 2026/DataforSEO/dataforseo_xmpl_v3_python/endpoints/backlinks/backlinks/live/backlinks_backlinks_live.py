"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/backlinks/backlinks/live
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
        'mode': 'as_is',
        'filters': [
            'dofollow',
            '=',
            True
        ],
        'limit': 5
    })
try:
    response = client.post('/v3/backlinks/backlinks/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
