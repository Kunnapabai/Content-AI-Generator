"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/on_page/keyword_density
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'id': '09161533-2692-0216-0000-952be01f5070',
        'url': 'https://dataforseo.com/',
        'keyword_length': 2,
        'filters': [
            'frequency',
            '>',
            5
        ],
        'order_by': [
            'frequency,desc'
        ],
        'limit': 20
    })
try:
    response = client.post('/v3/on_page/keyword_density', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
