"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/keywords_data/dataforseo_trends/demography/live
@see https://docs.dataforseo.com/v3/keywords_data/dataforseo_trends/demography/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'keywords': [
            'seo api',
            'rank api'
        ],
        'location_code': 2840,
        'type': 'web'
    })
try:
    response = client.post('/v3/keywords_data/dataforseo_trends/demography/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
