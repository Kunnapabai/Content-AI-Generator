"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/on_page/resources
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'id': '08101204-0696-0216-0000-644a7b21a48a',
        'filters': [
            [
                'resource_type',
                '=',
                'image'
            ],
            'and',
            [
                'size',
                '>',
                100000
            ]
        ],
        'order_by': [
            'size,desc'
        ],
        'limit': 5
    })
try:
    response = client.post('/v3/on_page/resources', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
