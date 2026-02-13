"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/content_generation/generate/live
@see https://docs.dataforseo.com/v3/content_generation/generate/live/
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'text': 'SEO is',
        'max_new_tokens': 100,
        'repetition_penalty': 1.2,
        'stop_words': [
            '
'
        ],
        'creativity_index': 1,
        'avoid_starting_words': [
            'SEO',
            'search engine optimization',
            'SEO is'
        ]
    })
try:
    response = client.post('/v3/content_generation/generate/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
