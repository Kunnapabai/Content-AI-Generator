"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/backlinks/bulk_backlinks/live
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
            'forbes.com',
            'cnn.com',
            'bbc.com',
            'yelp.com',
            'https://www.apple.com/iphone/',
            'https://ahrefs.com/blog/',
            'ibm.com',
            'https://variety.com/',
            'https://stackoverflow.com/',
            'www.trustpilot.com'
        ]
    })
try:
    response = client.post('/v3/backlinks/bulk_backlinks/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
