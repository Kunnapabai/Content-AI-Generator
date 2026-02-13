"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/business_data/tripadvisor/reviews/task_post
@see https://docs.dataforseo.com/v3/business_data/tripadvisor/reviews/task_post
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'url_path': 'Hotel_Review-g60763-d23462501-Reviews-Margaritaville_Times_Square-New_York_City_New_York.html',
        'location_code': 1003854,
        'depth': 50
    })
try:
    response = client.post('/v3/business_data/tripadvisor/reviews/task_post', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
