"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/backlinks/history/live
@see https://docs.dataforseo.com/v3/backlinks/history/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'target': 'cnn.com',
        'date_from': '2020-08-01',
        'date_to': '2021-01-01'
    })
try:
    response = client.post('/v3/backlinks/history/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
