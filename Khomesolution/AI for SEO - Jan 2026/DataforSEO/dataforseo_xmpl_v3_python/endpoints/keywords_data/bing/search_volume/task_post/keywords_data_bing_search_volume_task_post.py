"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/keywords_data/bing/search_volume/task_post
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'location_name': 'United States',
        'language_name': 'English',
        'keywords': [
            'average page rpm adsense',
            'adsense blank ads how long',
            'leads and prospects'
        ]
    })
try:
    response = client.post('/v3/keywords_data/bing/search_volume/task_post', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
