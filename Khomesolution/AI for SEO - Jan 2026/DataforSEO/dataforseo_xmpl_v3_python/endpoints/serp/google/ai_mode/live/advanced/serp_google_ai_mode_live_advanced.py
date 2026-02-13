"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/serp/google/ai_mode/live/advanced
@see https://docs.dataforseo.com/v3/serp/google/ai_mode/live/advanced
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'language_name': 'English',
        'location_name': 'London,England,United Kingdom',
        'keyword': 'rank checker'
    })
try:
    response = client.post('/v3/serp/google/ai_mode/live/advanced', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
