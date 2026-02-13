"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/serp/google/search_by_image/task_post
@see https://docs.dataforseo.com/v3/serp/google/search_by_image/task_post
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
        'image_url': 'https://dataforseo.com/wp-content/uploads/2016/11/data_for_seo_light_429.png',
        'device': 'desktop',
        'tag': 'some_string_123'
    })
try:
    response = client.post('/v3/serp/google/search_by_image/task_post', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
