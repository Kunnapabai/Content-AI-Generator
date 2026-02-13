"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/google/categories_for_domain/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/google/categories_for_domain/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'target': 'dataforseo.com',
        'language_code': 'en',
        'location_name': 'United States',
        'item_types': [
            'paid',
            'organic',
            'featured_snippet',
            'local_pack'
        ],
        'limit': 3
    })
try:
    response = client.post('/v3/dataforseo_labs/google/categories_for_domain/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
