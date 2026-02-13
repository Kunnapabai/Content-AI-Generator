"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/on_page/microdata
@see https://docs.dataforseo.com/v3/on_page/microdata
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'id': '03131749-0696-0216-0000-a8813ab0d856',
        'url': 'https://dataforseo.com/apis'
    })
try:
    response = client.post('/v3/on_page/microdata', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
