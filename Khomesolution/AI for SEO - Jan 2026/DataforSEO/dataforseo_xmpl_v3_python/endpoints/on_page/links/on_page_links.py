"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/on_page/links
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'id': '08101056-0696-0216-0000-721423f84e3d',
        'filters': [
            [
                'dofollow',
                '=',
                True
            ],
            'and',
            [
                'direction',
                '=',
                'external'
            ]
        ],
        'limit': 3
    })
try:
    response = client.post('/v3/on_page/links', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
