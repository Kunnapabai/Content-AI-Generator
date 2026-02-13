"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/business_data/tripadvisor/search/task_post
@see https://docs.dataforseo.com/v3/business_data/tripadvisor/search/task_post
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'keyword': 'pizza',
        'location_code': 1003854,
        'depth': 60
    })
try:
    response = client.post('/v3/business_data/tripadvisor/search/task_post', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
