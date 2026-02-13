"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/keywords_data/google_trends/explore/task_post
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'date_from': '2019-01-01',
        'date_to': '2020-01-01',
        'keywords': [
            'seo api',
            'rank api'
        ]
    })
try:
    response = client.post('/v3/keywords_data/google_trends/explore/task_post', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
