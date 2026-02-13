"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/serp/yahoo/organic/live/html
@see https://docs.dataforseo.com/v3/serp/yahoo/organic/live/html
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'device': 'mobile',
        'language_name': 'English',
        'location_name': 'London,England,United Kingdom',
        'keyword': 'rank checker'
    })
try:
    response = client.post('/v3/serp/yahoo/organic/live/html', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
