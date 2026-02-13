"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/backlinks/domain_pages/live
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
        'limit': 5,
        'filters': [
            [
                'page_summary.backlinks',
                '>',
                5
            ],
            'and',
            [
                'page',
                'like',
                '%sites%'
            ]
        ]
    })
try:
    response = client.post('/v3/backlinks/domain_pages/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
