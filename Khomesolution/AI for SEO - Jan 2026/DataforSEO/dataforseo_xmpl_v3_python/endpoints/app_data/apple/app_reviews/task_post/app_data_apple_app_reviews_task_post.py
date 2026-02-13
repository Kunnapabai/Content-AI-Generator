"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/app_data/apple/app_reviews/task_post
@see https://docs.dataforseo.com/v3/app_data/apple/app_reviews/task_post/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'app_id': '835599320',
        'location_code': 2840,
        'language_code': 'en',
        'depth': 200
    })
try:
    response = client.post('/v3/app_data/apple/app_reviews/task_post', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
