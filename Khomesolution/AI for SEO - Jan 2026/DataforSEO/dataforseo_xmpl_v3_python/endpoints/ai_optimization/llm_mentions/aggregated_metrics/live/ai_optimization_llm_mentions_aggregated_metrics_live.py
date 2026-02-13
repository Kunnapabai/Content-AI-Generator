"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/ai_optimization/llm_mentions/aggregated_metrics/live
@see https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/aggregated_metrics/live
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../')))
from lib.client import RestClient
from lib.config import username, password
client = RestClient(username, password)

post_data = []
post_data.append({
        'language_code': 'es',
        'location_code': 2840,
        'platform': 'google',
        'target': [
            {
                'domain': 'en.wikipedia.org',
                'search_filter': 'exclude'
            },
            {
                'keyword': 'bmw',
                'search_scope': [
                    'answer'
                ]
            }
        ],
        'initial_dataset_filters': [
            [
                'ai_search_volume',
                '>',
                10
            ]
        ],
        'internal_list_limit': 10
    })
try:
    response = client.post('/v3/ai_optimization/llm_mentions/aggregated_metrics/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
