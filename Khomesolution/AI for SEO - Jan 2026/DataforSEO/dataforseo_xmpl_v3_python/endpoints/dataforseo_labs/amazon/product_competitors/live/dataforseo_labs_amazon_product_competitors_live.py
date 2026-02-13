"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/amazon/product_competitors/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/amazon/product_competitors/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'asin': '019005476X',
        'language_name': 'English',
        'location_code': 2840,
        'limit': 3
    })
try:
    response = client.post('/v3/dataforseo_labs/amazon/product_competitors/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
