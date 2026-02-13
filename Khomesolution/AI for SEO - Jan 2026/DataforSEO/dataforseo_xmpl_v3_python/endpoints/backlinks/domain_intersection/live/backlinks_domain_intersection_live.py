"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/backlinks/domain_intersection/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'targets': {
            1: 'adidas.com',
            2: 'nike.com'
        },
        'include_subdomains': False,
        'exclude_targets': [
            'puma.com'
        ],
        'limit': 5,
        'order_by': [
            '1.backlinks,desc'
        ],
        'exclude_internal_backlinks': True
    })
try:
    response = client.post('/v3/backlinks/domain_intersection/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
