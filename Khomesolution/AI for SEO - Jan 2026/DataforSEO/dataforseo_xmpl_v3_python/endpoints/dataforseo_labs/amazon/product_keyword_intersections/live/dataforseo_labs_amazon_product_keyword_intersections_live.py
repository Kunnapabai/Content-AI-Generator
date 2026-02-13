"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/amazon/product_keyword_intersections/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/amazon/product_keyword_intersections/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'asins': {
            1: 'B094PS5RZQ',
            2: 'B082G5SPR5',
            3: 'B082G5BDNC',
            4: 'B0086UK7IQ'
        },
        'language_name': 'English',
        'location_code': 2840,
        'intersection_mode': 'intersect'
    })
try:
    response = client.post('/v3/dataforseo_labs/amazon/product_keyword_intersections/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
