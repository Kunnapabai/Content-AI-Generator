"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/merchant/amazon/sellers/task_post
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'language_code': 'en_US',
        'location_code': 9004056,
        'asin': 'B07D528W98'
    })
try:
    response = client.post('/v3/merchant/amazon/sellers/task_post', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
