"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live
@see https://docs.dataforseo.com/v3/keywords\_data/google\_ads/search\_volume/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'language_code': 'en',
        'location_code': 2840,
        'keywords': [
            'buy laptop',
            'cheap laptops for sale',
            'purchase laptop'
        ],
        'date_from': '2021-08-01'
    })
try:
    response = client.post('/v3/keywords_data/google_ads/search_volume/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
