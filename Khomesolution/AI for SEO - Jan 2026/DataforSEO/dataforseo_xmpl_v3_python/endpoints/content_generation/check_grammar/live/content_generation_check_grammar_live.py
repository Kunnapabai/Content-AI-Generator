"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/content_generation/check_grammar/live
@see https://docs.dataforseo.com/v3/content_generation/check_grammar/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'text': 'Hello, my name is John! And I\'m very glad to work with you toda',
        'language_code': 'en-US'
    })
try:
    response = client.post('/v3/content_generation/check_grammar/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
