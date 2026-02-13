"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/amazon/ranked_keywords/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/amazon/ranked_keywords/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'asin': 'B07GBZ4Q68',
        'location_code': 2840,
        'language_code': 'en',
        'limit': 3
    })
try:
    response = client.post('/v3/dataforseo_labs/amazon/ranked_keywords/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
