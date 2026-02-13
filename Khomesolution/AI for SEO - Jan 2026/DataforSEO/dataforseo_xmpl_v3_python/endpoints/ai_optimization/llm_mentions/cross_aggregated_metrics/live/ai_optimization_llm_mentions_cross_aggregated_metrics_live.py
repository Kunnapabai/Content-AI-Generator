"""
Method: POST
Endpoint: https://api.dataforseo.com/v3/ai_optimization/llm_mentions/cross_aggregated_metrics/live
@see https://docs.dataforseo.com/v3/ai_optimization/llm_mentions/cross_aggregated_metrics/live
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
        'targets': [
            {
                'aggregation_key': 'chat_gpt',
                'target': [
                    {
                        'keyword': 'chat gpt'
                    }
                ]
            },
            {
                'aggregation_key': 'claude',
                'target': [
                    {
                        'keyword': 'claude'
                    }
                ]
            },
            {
                'aggregation_key': 'gemini',
                'target': [
                    {
                        'keyword': 'gemini'
                    }
                ]
            },
            {
                'aggregation_key': 'perplexity',
                'target': [
                    {
                        'keyword': 'perplexity',
                        'search_filter': 'include'
                    }
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
        'internal_list_limit': 5
    })
try:
    response = client.post('/v3/ai_optimization/llm_mentions/cross_aggregated_metrics/live', post_data)
    print(response)
    # do something with post result
except Exception as e:
    print(f'An error occurred: {e}')
