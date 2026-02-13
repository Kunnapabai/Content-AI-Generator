"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/dataforseo_labs/google/categories_for_keywords/live
@see https://docs.dataforseo.com/v3/dataforseo_labs/google/categories_for_keywords/live/
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
            'albert einstein'
        ],
        'language_name': 'English'
    })
try:
    response = client.post('/v3/dataforseo_labs/google/categories_for_keywords/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
