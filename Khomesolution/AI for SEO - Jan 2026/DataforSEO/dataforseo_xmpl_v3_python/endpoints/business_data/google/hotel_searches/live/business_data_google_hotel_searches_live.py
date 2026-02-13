"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/business_data/google/hotel_searches/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'location_name': 'New York,New York,United States',
        'language_name': 'English',
        'keyword': 'cheap hotel'
    })
try:
    response = client.post('/v3/business_data/google/hotel_searches/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
