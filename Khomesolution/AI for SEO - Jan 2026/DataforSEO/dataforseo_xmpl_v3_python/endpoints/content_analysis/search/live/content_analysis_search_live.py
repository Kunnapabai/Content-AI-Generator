"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/content_analysis/search/live
@see https://docs.dataforseo.com/v3/content_analysis/search/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'keyword': 'logitech',
        'content_mode': 'as_is',
        'page_type': [
            'ecommerce'
        ],
        'filters': [
            [
                'language',
                '=',
                'en'
            ],
            'and',
            [
                'content_info.rating.rating_value',
                '>',
                0
            ]
        ],
        'order_by': [
            'main_domain,asc'
        ],
        'limit': 3
    })
try:
    response = client.post('/v3/content_analysis/search/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
