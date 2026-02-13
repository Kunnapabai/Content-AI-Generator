"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/business_data/business_listings/search/live
@see https://docs.dataforseo.com/v3/business_data/business_listings/search/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'categories': [
            'pizza_restaurant'
        ],
        'description': 'pizza',
        'title': 'pizza',
        'is_claimed': True,
        'location_coordinate': '53.476225,-2.243572,10',
        'order_by': [
            'rating.value,desc'
        ],
        'filters': [
            [
                'rating.value',
                '>',
                3
            ]
        ],
        'limit': 3
    })
try:
    response = client.post('/v3/business_data/business_listings/search/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
