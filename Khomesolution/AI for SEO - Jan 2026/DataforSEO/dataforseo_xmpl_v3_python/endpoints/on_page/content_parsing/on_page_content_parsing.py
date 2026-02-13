"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/on_page/content_parsing
@see https://docs.dataforseo.com/v3/on_page/content_parsing/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'id': '11161719-0696-0216-1000-8e2705395d43',
        'url': 'https://dataforseo.com/'
    })
try:
    response = client.post('/v3/on_page/content_parsing', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
