"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/ai_optimization/llm_mentions/top_pages/live
@see https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/top_pages/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'language_code': 'en',
        'location_code': 2840,
        'platform': 'google',
        'target': [
            {
                'keyword': 'bmw',
                'search_scope': [
                    'answer'
                ]
            },
            {
                'keyword': 'auto',
                'search_scope': [
                    'question'
                ],
                'match_type': 'partial_match'
            }
        ],
        'links_scope': 'sources',
        'initial_dataset_filters': [
            [
                'ai_search_volume',
                '>',
                10
            ]
        ],
        'items_list_limit': 3,
        'internal_list_limit': 2
    })
try:
    response = client.post('/v3/ai_optimization/llm_mentions/top_pages/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
