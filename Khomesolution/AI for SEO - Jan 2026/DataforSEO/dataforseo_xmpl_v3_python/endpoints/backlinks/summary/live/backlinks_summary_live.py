"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/backlinks/summary/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'target': 'explodingtopics.com',
        'internal_list_limit': 10,
        'include_subdomains': True,
        'backlinks_filters': [
            'dofollow',
            '=',
            True
        ],
        'backlinks_status_type': 'all'
    })
try:
    response = client.post('/v3/backlinks/summary/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
