"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/backlinks/bulk_pages_summary/live
@see https://api.dataforseo.com/v3/backlinks/bulk_pages_summary/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'targets': [
            'https://dataforseo.com/',
            'https://dataforseo.com/about-us'
        ]
    })
try:
    response = client.post('/v3/backlinks/bulk_pages_summary/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
