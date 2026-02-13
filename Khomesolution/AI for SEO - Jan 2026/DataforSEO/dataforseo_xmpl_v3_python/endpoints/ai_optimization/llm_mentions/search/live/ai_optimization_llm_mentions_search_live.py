"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/ai_optimization/llm_mentions/search/live
@see https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/search/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'language_name': 'English',
        'location_code': 2840,
        'target': [
            {
                'domain': 'dataforseo.com',
                'search_filter': 'exclude'
            },
            {
                'keyword': 'bmw',
                'search_scope': [
                    'answer'
                ]
            }
        ],
        'platform': 'google',
        'filters': [
            [
                'ai_search_volume',
                '>',
                1000
            ]
        ],
        'order_by': [
            'ai_search_volume,desc'
        ],
        'limit': 3
    })
try:
    response = client.post('/v3/ai_optimization/llm_mentions/search/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
